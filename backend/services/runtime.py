"""Shared local runtime services for the Fast retrieval profile."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from services.bm25_index import BM25IndexService
from services.dense_index import DenseIndexError, DenseIndexService
from services.embedder import QwenEmbeddingService
from services.folder_sync import FolderSyncService
from services.indexing_queue import BackgroundIndexQueue
from services.ingestion import DocumentIngestionService
from services.metadata_store import MetadataStore
from services.quality_retriever import QualityRetriever
from services.reranker import LocalReranker
from services.settings import settings

DATA_ROOT = settings.data_dir
metadata_store = MetadataStore(DATA_ROOT / "metadata.sqlite")
embedding_service = QwenEmbeddingService()

MODEL_PATH = os.getenv("DOCMIND_EMBEDDING_MODEL_PATH")
embedding_logger = logging.getLogger("docmind.embedding")
if MODEL_PATH and Path(MODEL_PATH).is_dir():
    try:
        embedding_logger.info("[EMBED] loading local model path=%s", MODEL_PATH)
        embedding_service.load_local_model(MODEL_PATH)
        embedding_logger.info(
            "[EMBED] model ready name=%s dimension=%d",
            embedding_service.model_name,
            embedding_service.embedding_dimension,
        )
    except Exception:
        embedding_logger.exception(
            "[EMBED] local model was not loaded path=%s",
            MODEL_PATH,
        )
elif MODEL_PATH:
    embedding_logger.warning("[EMBED] configured model path does not exist path=%s", MODEL_PATH)
else:
    embedding_logger.warning("[EMBED] no local model configured; dense indexing is disabled")

try:
    dense_index: DenseIndexService | None = DenseIndexService(
        DATA_ROOT / "indexes" / "fast",
        embedding_service,
        metadata_store,
    )
except DenseIndexError as error:
    print(f"[DenseIndex] Fast retrieval is unavailable: {error}")
    dense_index = None

bm25_index = BM25IndexService(DATA_ROOT / "indexes" / "quality", metadata_store)
reranker = LocalReranker()
RERANKER_PATH = os.getenv("DOCMIND_RERANKER_MODEL_PATH")
if RERANKER_PATH and Path(RERANKER_PATH).is_dir():
    try:
        reranker.load_local_model(RERANKER_PATH)
    except Exception as error:
        print(f"[Reranker] Local BGE model was not loaded: {error}")

quality_retriever: QualityRetriever | None = None
if dense_index is not None:
    quality_retriever = QualityRetriever(dense_index, bm25_index, reranker)


logger = logging.getLogger("docmind.index")


def index_document(document_id: str | list[dict], force_rebuild: bool = False) -> int:
    """Build both P3 indexes after a successful extraction."""
    document_label = document_id if isinstance(document_id, str) else "<ingestion-batch>"
    if dense_index is None or not dense_index.model_ready:
        logger.warning(
            "[INDEX] skipped document=%s reason=dense_embedding_model_not_ready",
            document_label,
        )
        return 0
    started_at = time.perf_counter()
    mode = "incremental" if isinstance(document_id, str) and not force_rebuild else "full"
    logger.info(
        "[INDEX] start document=%s mode=%s stages=embedding,dense,bm25",
        document_label,
        mode,
    )
    dense_started_at = time.perf_counter()
    if isinstance(document_id, str) and not force_rebuild:
        dense_count = dense_index.upsert_document(document_id)
    else:
        dense_count = dense_index.index_document(document_id)  # type: ignore[arg-type]
    logger.info(
        "[INDEX] dense complete document=%s chunks=%d elapsed_ms=%.1f",
        document_label,
        dense_count,
        (time.perf_counter() - dense_started_at) * 1000,
    )
    bm25_started_at = time.perf_counter()
    lexical_count = bm25_index.index_document(document_id)  # type: ignore[arg-type]
    logger.info(
        "[INDEX] bm25 complete document=%s chunks=%d elapsed_ms=%.1f total_elapsed_ms=%.1f",
        document_label,
        lexical_count,
        (time.perf_counter() - bm25_started_at) * 1000,
        (time.perf_counter() - started_at) * 1000,
    )
    return lexical_count

ingestion_service = DocumentIngestionService(
    DATA_ROOT,
    metadata_store=metadata_store,
)

indexing_queue = BackgroundIndexQueue(ingestion_service, index_document)


def queue_document_index(document_id: str, force_rebuild: bool = False) -> bool:
    """Schedule a source document only when local embeddings are available."""
    if dense_index is None or not dense_index.model_ready:
        logger.warning(
            "[INDEX_QUEUE] not queued document=%s reason=dense_embedding_model_not_ready",
            document_id,
        )
        return False
    return indexing_queue.enqueue(document_id, force_rebuild=force_rebuild)


def queue_catalog_rebuild(document_ids: list[str]) -> bool:
    """Schedule one safe rebuild for source replacements or removals."""
    if dense_index is None or not dense_index.model_ready:
        logger.warning("[INDEX_QUEUE] full rebuild not queued reason=dense_embedding_model_not_ready")
        return False
    return indexing_queue.enqueue_rebuild(document_ids)


folder_sync_service = FolderSyncService(
    settings.source_dir,
    ingestion_service,
    metadata_store=metadata_store,
    queue_document=queue_document_index,
    queue_rebuild=queue_catalog_rebuild,
)
if settings.sync_on_startup:
    folder_sync_service.start_background()
