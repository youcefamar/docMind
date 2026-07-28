"""Profile the offline DocMind runtime on the current machine.

This script intentionally reports the backend that was actually loaded. A
deterministic embedding fallback is useful for validating the pipeline, but its
numbers must not be presented as Qwen embedding performance.

Examples (PowerShell, from ``backend``)::

    python scripts/profile_local.py --sync --rebuild-indexes
    python scripts/profile_local.py --profile fast --repetitions 5
    python scripts/profile_local.py --rebuild-indexes --max-index-chunks 300
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")
sys.path.insert(0, str(REPO_ROOT / "backend"))

from models.contracts import RetrievalProfile, RetrievalResult  # noqa: E402
from services.bm25_index import BM25IndexService  # noqa: E402
from services.dense_index import DenseIndexService  # noqa: E402
from services.embedder import QwenEmbeddingService  # noqa: E402
from services.folder_sync import FolderSyncService  # noqa: E402
from services.ingestion import DocumentIngestionService  # noqa: E402
from services.llm import LLMService  # noqa: E402
from services.metadata_store import MetadataStore  # noqa: E402
from services.quality_retriever import reciprocal_rank_fusion  # noqa: E402
from services.reranker import LocalReranker  # noqa: E402
from services.settings import settings  # noqa: E402


def _resolve_path(value: str | None, fallback: Path) -> Path:
    if not value:
        return fallback.resolve()
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate if candidate.exists() else fallback.resolve()
    for base in (Path.cwd(), REPO_ROOT, REPO_ROOT / "backend"):
        resolved = (base / candidate).resolve()
        if resolved.exists():
            return resolved
    return fallback.resolve()


def _size_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    if path.is_dir():
        return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
    return 0


def _rss_mb() -> float | None:
    """Return current/peak process RSS without adding a runtime dependency."""
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = Counters()
        counters.cb = ctypes.sizeof(Counters)
        process = ctypes.windll.kernel32.GetCurrentProcess()
        get_info = ctypes.windll.psapi.GetProcessMemoryInfo
        get_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        get_info.restype = wintypes.BOOL
        get_info(process, ctypes.byref(counters), counters.cb)
        return round(counters.PeakWorkingSetSize / (1024 * 1024), 2)

    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        divisor = 1024 * 1024 if sys.platform == "darwin" else 1024
        return round(usage.ru_maxrss / divisor, 2)
    except (ImportError, AttributeError):
        return None


def _summarize(values: Iterable[float]) -> dict[str, float | int | None]:
    samples = [round(float(value), 3) for value in values]
    if not samples:
        return {"count": 0, "min_ms": None, "median_ms": None, "p95_ms": None, "max_ms": None}
    ordered = sorted(samples)
    p95_index = min(len(ordered) - 1, max(0, math.ceil(len(ordered) * 0.95) - 1))
    return {
        "count": len(samples),
        "min_ms": ordered[0],
        "median_ms": round(statistics.median(ordered), 3),
        "p95_ms": ordered[p95_index],
        "max_ms": ordered[-1],
    }


def _measure(function: Callable[[], Any], repetitions: int) -> tuple[Any, dict[str, float | int | None]]:
    samples: list[float] = []
    result = None
    for _ in range(repetitions):
        started = time.perf_counter()
        result = function()
        samples.append((time.perf_counter() - started) * 1000)
    return result, _summarize(samples)


def _artifact(path: Path, kind: str) -> dict[str, Any]:
    exists = path.is_file() if kind == "file" else path.is_dir()
    return {
        "path": str(path),
        "exists": exists,
        "size_mb": round(_size_bytes(path) / (1024 * 1024), 2) if exists else 0,
    }


def _source_dict(result: RetrievalResult, metadata_store: MetadataStore) -> dict[str, Any]:
    document = metadata_store.get_document(result.document_id)
    return {
        "doc_id": result.document_id,
        "chunk_id": result.chunk_id,
        "filename": result.filename,
        "category": result.category,
        "page_number": int(result.location_value) if result.location_type == "page" else 1,
        "total_pages": document.total_pages if document else 1,
        "excerpt": result.text,
        "similarity": result.score,
        "rank": result.rank,
        "location_type": result.location_type,
        "location_value": result.location_value,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", help="Override the local persistence root")
    parser.add_argument("--source-dir", help="Override the managed knowledge folder")
    parser.add_argument("--question", default="What information is available in the indexed documents?")
    parser.add_argument("--profile", choices=("fast", "quality", "both"), default="both")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--sync", action="store_true", help="Synchronize the managed folder before profiling")
    parser.add_argument("--rebuild-indexes", action="store_true", help="Rebuild FAISS and BM25 before profiling")
    parser.add_argument(
        "--max-index-chunks",
        type=int,
        default=0,
        help="Limit rebuild scope for a bounded experiment; 0 uses every stored chunk",
    )
    parser.add_argument("--skip-generation", action="store_true")
    parser.add_argument("--output", help="JSON output path (default: data/profiling/profile_local.json)")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    repetitions = max(1, args.repetitions)
    data_dir = _resolve_path(args.data_dir or os.getenv("DOCMIND_DATA_DIR"), REPO_ROOT / "data")
    source_dir = _resolve_path(
        args.source_dir or os.getenv("DOCMIND_SOURCE_DIR"), data_dir / "knowledge"
    )
    output_path = _resolve_path(args.output, data_dir / "profiling" / "profile_local.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    process_started = time.perf_counter()
    memory_samples: list[float] = []
    notes: list[str] = []

    embedding_path = _resolve_path(
        os.getenv("DOCMIND_EMBEDDING_MODEL_PATH"), REPO_ROOT / "missing-embedding-model"
    )
    llm_env_path = _resolve_path(
        os.getenv("DOCMIND_LLM_MODEL_PATH"), REPO_ROOT / "missing-llm-model.gguf"
    )
    repo_llm_path = REPO_ROOT / "backend" / "models" / "qwen3-4b-q4_k_m.gguf"
    llm_path = llm_env_path if llm_env_path.is_file() else repo_llm_path
    if llm_path == repo_llm_path and not llm_env_path.is_file():
        notes.append("DOCMIND_LLM_MODEL_PATH was unavailable; the repository GGUF artifact was used.")

    artifacts = {
        "embedding_model": _artifact(embedding_path, "directory"),
        "llm_model": _artifact(llm_path, "file"),
    }
    if not artifacts["embedding_model"]["exists"]:
        notes.append("No local embedding weights were found; embedding timings use the deterministic fallback.")

    metadata_store = MetadataStore(data_dir / "metadata.sqlite")
    embedding_service = QwenEmbeddingService()
    model_load_ms: dict[str, dict[str, Any]] = {}
    if artifacts["embedding_model"]["exists"]:
        started = time.perf_counter()
        try:
            embedding_service.load_local_model(str(embedding_path))
            model_load_ms["embedding"] = {
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                "backend": "sentence-transformers-local",
                "ready": embedding_service.is_ready,
            }
        except Exception as error:
            notes.append(f"Embedding model load failed; fallback used: {error}")
            model_load_ms["embedding"] = {"elapsed_ms": None, "backend": "fallback", "ready": False, "error": str(error)}
    else:
        model_load_ms["embedding"] = {"elapsed_ms": 0.0, "backend": "deterministic-fallback", "ready": False}
    memory_samples.append(_rss_mb() or 0.0)

    dense_index = DenseIndexService(data_dir / "indexes" / "fast", embedding_service, metadata_store)
    bm25_index = BM25IndexService(data_dir / "indexes" / "quality", metadata_store)
    ingestion_service = DocumentIngestionService(data_dir, metadata_store=metadata_store)
    sync_status = None
    if args.sync:
        sync_service = FolderSyncService(source_dir, ingestion_service, metadata_store=metadata_store)
        sync_started = time.perf_counter()
        sync_status = sync_service.sync()
        sync_status["elapsed_ms"] = round((time.perf_counter() - sync_started) * 1000, 3)
        memory_samples.append(_rss_mb() or 0.0)

    index_build = {"dense_chunks": len(dense_index.chunk_ids), "lexical_chunks": len(bm25_index.chunk_ids)}
    if args.rebuild_indexes:
        started = time.perf_counter()
        chunks = metadata_store.list_chunks()
        if args.max_index_chunks > 0:
            chunks = chunks[: args.max_index_chunks]
            notes.append(
                f"Index rebuild was limited to {len(chunks)} chunks; retrieval latency is not a full-corpus measurement."
            )
        dense_count = dense_index.rebuild(chunks)
        bm25_count = bm25_index.rebuild(chunks)
        index_build = {
            "dense_chunks": dense_count,
            "lexical_chunks": bm25_count,
            "scope": "limited" if args.max_index_chunks > 0 else "full",
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        }
        memory_samples.append(_rss_mb() or 0.0)

    reranker = LocalReranker()
    reranker_path = _resolve_path(
        os.getenv("DOCMIND_RERANKER_MODEL_PATH"), REPO_ROOT / "missing-reranker-model"
    )
    reranker_load = {"ready": False, "backend": "not_configured", "elapsed_ms": 0.0}
    if reranker_path.is_dir() and any(reranker_path.iterdir()):
        started = time.perf_counter()
        try:
            reranker.load_local_model(str(reranker_path))
            reranker_load = {
                "ready": reranker.is_ready,
                "backend": "cross-encoder-local",
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            }
        except Exception as error:
            reranker_load = {"ready": False, "backend": "load_failed", "elapsed_ms": None, "error": str(error)}
            notes.append(f"Reranker load failed: {error}")

    llm_load_started = time.perf_counter()
    llm_service = LLMService(model_path=str(llm_path) if llm_path.is_file() else "", auto_load=True)
    model_load_ms["llm"] = {
        "elapsed_ms": round((time.perf_counter() - llm_load_started) * 1000, 3),
        "backend": llm_service.backend,
        "ready": llm_service.model_ready,
        "model_name": llm_service.model_name,
    }
    memory_samples.append(_rss_mb() or 0.0)
    if not llm_service.model_ready:
        notes.append("Local GGUF generation was unavailable; generation timing uses the extractive fallback.")

    stages: dict[str, dict[str, Any]] = {}
    query_vector, stages["query_embedding"] = _measure(
        lambda: embedding_service.generate_embeddings([args.question])[0], repetitions
    )
    memory_samples.append(_rss_mb() or 0.0)

    dense_results, stages["faiss_search"] = _measure(
        lambda: dense_index.search_vector(query_vector, top_k=settings.fast_top_k), repetitions
    )
    memory_samples.append(_rss_mb() or 0.0)
    lexical_results, stages["bm25_search"] = _measure(
        lambda: bm25_index.search_ids(args.question, top_k=settings.quality_candidate_k), repetitions
    )
    memory_samples.append(_rss_mb() or 0.0)
    fused_results, stages["rrf_fusion"] = _measure(
        lambda: reciprocal_rank_fusion(
            [[(result.chunk_id, result.score) for result in dense_results], lexical_results],
            top_k=settings.quality_candidate_k,
        ),
        repetitions,
    )
    memory_samples.append(_rss_mb() or 0.0)

    candidates = [
        metadata_store.get_chunk(chunk_id).text
        for chunk_id, _score in fused_results
        if metadata_store.get_chunk(chunk_id)
    ]
    if reranker.is_ready:
        _rerank_result, stages["reranker"] = _measure(
            lambda: reranker.score(args.question, candidates), repetitions
        )
    else:
        stages["reranker"] = {"count": 0, "min_ms": None, "median_ms": None, "p95_ms": None, "max_ms": None}

    def fast_retrieval() -> list[RetrievalResult]:
        return dense_index.search(args.question, top_k=settings.fast_top_k)

    def quality_retrieval() -> list[RetrievalResult]:
        dense = dense_index.search(args.question, top_k=settings.quality_candidate_k)
        dense_ranking = [(result.chunk_id, result.score) for result in dense]
        lexical = bm25_index.search_ids(args.question, top_k=settings.quality_candidate_k)
        fused = reciprocal_rank_fusion([dense_ranking, lexical], top_k=settings.quality_candidate_k)
        if reranker.is_ready:
            scores = reranker.score(
                args.question,
                [metadata_store.get_chunk(chunk_id).text for chunk_id, _ in fused if metadata_store.get_chunk(chunk_id)],
            )
            fused = [item for item, _score in sorted(zip(fused, scores), key=lambda pair: pair[1], reverse=True)]
        results = []
        for rank, (chunk_id, score) in enumerate(fused[: settings.quality_final_k], start=1):
            chunk = metadata_store.get_chunk(chunk_id)
            if not chunk:
                continue
            document = metadata_store.get_document(chunk.document_id)
            if not document:
                continue
            results.append(
                RetrievalResult(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    text=chunk.text,
                    rank=rank,
                    score=float(score),
                    retrieval_profile=RetrievalProfile.QUALITY,
                    filename=document.filename,
                    category=document.category,
                    location_type=chunk.location_type,
                    location_value=chunk.location_value,
                )
            )
        return results

    profile_results: dict[str, Any] = {}
    selected_results: list[RetrievalResult] = []
    if args.profile in {"fast", "both"}:
        selected_results, profile_results["fast_retrieval"] = _measure(fast_retrieval, repetitions)
    if args.profile in {"quality", "both"}:
        quality_results, profile_results["quality_retrieval"] = _measure(quality_retrieval, repetitions)
        if args.profile == "quality":
            selected_results = quality_results

    generation = {"skipped": args.skip_generation}
    end_to_end: dict[str, Any] = {}
    if not args.skip_generation and selected_results:
        sources = [_source_dict(result, metadata_store) for result in selected_results]
        _answer, generation = _measure(
            lambda: llm_service.generate_answer(args.question, sources), repetitions
        )
        generation["backend"] = llm_service.backend
        generation["model_name"] = llm_service.model_name
        generation["last_generation_stats"] = llm_service.last_generation_stats

        def end_to_end_query() -> tuple[str, float, str]:
            results = fast_retrieval() if args.profile == "fast" else (
                quality_retrieval() if args.profile == "quality" else fast_retrieval()
            )
            return llm_service.generate_answer(
                args.question,
                [_source_dict(result, metadata_store) for result in results],
            )

        _end_result, end_to_end = _measure(end_to_end_query, repetitions)
        end_to_end["backend"] = llm_service.backend
        end_to_end["model_name"] = llm_service.model_name
        end_to_end["last_generation_stats"] = llm_service.last_generation_stats
    elif not args.skip_generation:
        notes.append("Generation was not measured because no retrieval results were available.")

    index_files = [
        data_dir / "indexes" / "fast" / "dense.faiss",
        data_dir / "indexes" / "fast" / "dense_mapping.json",
        data_dir / "indexes" / "quality" / "bm25.json",
    ]
    result = {
        "schema_version": 1,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "gpu_vram_mb": None,
            "peak_rss_mb": max(memory_samples or [0.0]),
        },
        "configuration": {
            "data_dir": str(data_dir),
            "source_dir": str(source_dir),
            "question": args.question,
            "profile": args.profile,
            "repetitions": repetitions,
            "embedding_model_name": embedding_service.model_name,
            "embedding_backend": "local" if embedding_service.is_ready else "deterministic-fallback",
            "llm_backend": llm_service.backend,
            "reranker_backend": reranker_load["backend"],
        },
        "artifacts": artifacts,
        "model_download": {
            "measured": False,
            "reason": "Artifacts were already cached; download timing belongs to the setup/API phase.",
        },
        "model_load": model_load_ms | {"reranker": reranker_load},
        "sync": sync_status,
        "index": index_build | {"files": [_artifact(path, "file") for path in index_files]},
        "stages": stages,
        "profiles": profile_results,
        "generation": generation,
        "end_to_end": end_to_end,
        "notes": notes,
        "script_elapsed_ms": round((time.perf_counter() - process_started) * 1000, 3),
    }
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nSaved profile to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
