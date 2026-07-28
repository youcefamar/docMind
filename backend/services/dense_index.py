"""Persistent FAISS dense retrieval for the P2 Fast profile."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np

try:
    import faiss
except ImportError:  # pragma: no cover - exercised only in incomplete installs.
    faiss = None

from models.contracts import ChunkRecord, RetrievalProfile, RetrievalResult
from services.metadata_store import MetadataStore


class DenseIndexError(RuntimeError):
    """Raised when the local dense index cannot be loaded or built."""


class DenseIndexService:
    """Maintain a cosine-similarity FAISS index and its chunk-ID mapping."""

    def __init__(
        self,
        index_root: str | Path,
        embedder: Any,
        metadata_store: MetadataStore,
    ):
        if faiss is None:
            raise DenseIndexError("faiss-cpu is required for dense retrieval")

        self.index_root = Path(index_root)
        self.index_root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_root / "dense.faiss"
        self.mapping_path = self.index_root / "dense_mapping.json"
        self.embedder = embedder
        self.metadata_store = metadata_store
        self.index: Optional[Any] = None
        self.chunk_ids: list[str] = []
        self._load()

    @property
    def model_revision(self) -> str:
        return getattr(self.embedder, "model_revision", None) or getattr(
            self.embedder, "model_name", "unknown"
        )

    @property
    def dimension(self) -> int:
        return int(self.embedder.embedding_dimension)

    @property
    def ready(self) -> bool:
        return self.index is not None and bool(self.chunk_ids)

    @property
    def model_ready(self) -> bool:
        return bool(getattr(self.embedder, "is_ready", True))

    def _load(self) -> None:
        if not self.index_path.is_file() or not self.mapping_path.is_file():
            return

        try:
            index = faiss.read_index(str(self.index_path))
            mapping = json.loads(self.mapping_path.read_text(encoding="utf-8"))
            if index.d != self.dimension or len(mapping.get("chunk_ids", [])) != index.ntotal:
                return
            self.index = index
            self.chunk_ids = mapping["chunk_ids"]
        except (OSError, ValueError, KeyError, RuntimeError):
            self.index = None
            self.chunk_ids = []

    @staticmethod
    def _normalize(vectors: list[list[float]]) -> np.ndarray:
        array = np.asarray(vectors, dtype="float32")
        if array.ndim != 2:
            raise DenseIndexError("Embedding output must be a two-dimensional matrix")
        norms = np.linalg.norm(array, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return array / norms

    def rebuild(self, chunks: list[ChunkRecord]) -> int:
        """Atomically rebuild the index from the supplied metadata chunks."""
        index = faiss.IndexFlatIP(self.dimension)
        if chunks:
            vectors = self._normalize(
                self.embedder.generate_embeddings([chunk.text for chunk in chunks])
            )
            if vectors.shape[1] != self.dimension:
                raise DenseIndexError(
                    f"Embedding dimension {vectors.shape[1]} does not match index dimension {self.dimension}"
                )
            index.add(vectors)

        self._persist(index, [chunk.id for chunk in chunks])
        self.index = index
        self.chunk_ids = [chunk.id for chunk in chunks]
        return len(chunks)

    def rebuild_from_store(self) -> int:
        return self.rebuild(self.metadata_store.list_chunks())

    def rebuild_batched(
        self,
        chunks: list[ChunkRecord],
        batch_size: int = 32,
        checkpoint_path: str | Path | None = None,
        progress_callback: Any = None,
    ) -> int:
        """Rebuild dense vectors in resumable batches.

        Each completed batch is persisted atomically. If a process is stopped
        between batches, the next invocation resumes only when the chunk
        fingerprint still matches; replacements or deletions automatically
        start a fresh rebuild.
        """
        if batch_size <= 0:
            raise DenseIndexError("batch_size must be greater than zero")

        ordered_chunks = list(chunks)
        fingerprint = self._chunks_fingerprint(ordered_chunks)
        checkpoint = Path(checkpoint_path) if checkpoint_path else None
        index = faiss.IndexFlatIP(self.dimension)
        indexed_ids: list[str] = []
        start = 0
        resumed = False

        if checkpoint and checkpoint.is_file() and self.index_path.is_file():
            try:
                payload = json.loads(checkpoint.read_text(encoding="utf-8"))
                checkpoint_ids = payload.get("chunk_ids", [])
                if (
                    payload.get("fingerprint") == fingerprint
                    and payload.get("total_chunks") == len(ordered_chunks)
                    and checkpoint_ids == [chunk.id for chunk in ordered_chunks[: len(checkpoint_ids)]]
                ):
                    restored = faiss.read_index(str(self.index_path))
                    if restored.d == self.dimension and restored.ntotal == len(checkpoint_ids):
                        index = restored
                        indexed_ids = list(checkpoint_ids)
                        start = len(indexed_ids)
                        resumed = start > 0
            except (OSError, ValueError, KeyError, TypeError, RuntimeError):
                pass

        started_at = time.perf_counter()
        for offset in range(start, len(ordered_chunks), batch_size):
            batch = ordered_chunks[offset : offset + batch_size]
            vectors = self._normalize(
                self.embedder.generate_embeddings([chunk.text for chunk in batch])
            )
            if vectors.shape[1] != self.dimension:
                raise DenseIndexError(
                    f"Embedding dimension {vectors.shape[1]} does not match index dimension {self.dimension}"
                )
            index.add(vectors)
            indexed_ids.extend(chunk.id for chunk in batch)
            self._persist(index, indexed_ids)
            if checkpoint:
                checkpoint.parent.mkdir(parents=True, exist_ok=True)
                temporary = checkpoint.with_suffix(checkpoint.suffix + ".tmp")
                temporary.write_text(
                    json.dumps(
                        {
                            "version": 1,
                            "fingerprint": fingerprint,
                            "total_chunks": len(ordered_chunks),
                            "chunk_ids": indexed_ids,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                os.replace(temporary, checkpoint)
            if progress_callback:
                progress_callback(
                    len(indexed_ids),
                    len(ordered_chunks),
                    (time.perf_counter() - started_at) * 1000,
                    resumed,
                )

        self.index = index
        self.chunk_ids = indexed_ids
        if checkpoint:
            checkpoint.unlink(missing_ok=True)
        return len(indexed_ids)

    @staticmethod
    def _chunks_fingerprint(chunks: list[ChunkRecord]) -> str:
        digest = hashlib.sha256()
        for chunk in chunks:
            digest.update(chunk.id.encode("utf-8"))
            digest.update(b"\0")
            digest.update(chunk.text.encode("utf-8"))
            digest.update(b"\0")
        return digest.hexdigest()

    def index_document(self, document_id: str) -> int:
        """Rebuild after ingestion; rebuild-all keeps replacement/delete atomic."""
        del document_id
        return self.rebuild_from_store()

    def _persist(self, index: Any, chunk_ids: list[str]) -> None:
        temporary_index = self.index_path.with_suffix(".faiss.tmp")
        temporary_mapping = self.mapping_path.with_suffix(".json.tmp")
        faiss.write_index(index, str(temporary_index))
        temporary_mapping.write_text(
            json.dumps(
                {
                    "version": 1,
                    "dimension": self.dimension,
                    "model_revision": self.model_revision,
                    "chunk_ids": chunk_ids,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        os.replace(temporary_index, self.index_path)
        os.replace(temporary_mapping, self.mapping_path)

    def search(
        self,
        question: str,
        category: Optional[str] = None,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        if not self.ready or top_k <= 0:
            return []

        query = self._normalize(self.embedder.generate_embeddings([question]))
        return self.search_vector(query[0].tolist(), category=category, top_k=top_k)

    def search_vector(
        self,
        query_vector: list[float],
        category: Optional[str] = None,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Search with a precomputed normalized query vector for profiling."""
        if not self.ready or top_k <= 0:
            return []

        query = self._normalize([query_vector])
        fetch_k = min(max(top_k * 5, top_k), self.index.ntotal)
        scores, ids = self.index.search(query, fetch_k)
        results: list[RetrievalResult] = []
        for score, index_id in zip(scores[0], ids[0]):
            if index_id < 0:
                continue
            chunk = self.metadata_store.get_chunk(self.chunk_ids[int(index_id)])
            if not chunk:
                continue
            document = self.metadata_store.get_document(chunk.document_id)
            if not document:
                continue
            if category and category.lower() != "all" and document.category.lower() != category.lower():
                continue
            results.append(
                RetrievalResult(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    text=chunk.text,
                    rank=len(results) + 1,
                    score=float(score),
                    retrieval_profile=RetrievalProfile.FAST,
                    filename=document.filename,
                    category=document.category,
                    location_type=chunk.location_type,
                    location_value=chunk.location_value,
                )
            )
            if len(results) == top_k:
                break
        return results
