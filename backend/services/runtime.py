"""Shared local runtime services for the Fast retrieval profile."""

from __future__ import annotations

import os
from pathlib import Path

from services.bm25_index import BM25IndexService
from services.dense_index import DenseIndexError, DenseIndexService
from services.embedder import QwenEmbeddingService
from services.ingestion import DocumentIngestionService
from services.metadata_store import MetadataStore
from services.quality_retriever import QualityRetriever
from services.reranker import LocalReranker

DATA_ROOT = Path(
    os.getenv(
        "DOCMIND_DATA_DIR",
        str(Path(__file__).resolve().parents[2] / "data"),
    )
)
metadata_store = MetadataStore(DATA_ROOT / "metadata.sqlite")
embedding_service = QwenEmbeddingService()

MODEL_PATH = os.getenv("DOCMIND_EMBEDDING_MODEL_PATH")
if MODEL_PATH and Path(MODEL_PATH).is_dir():
    try:
        embedding_service.load_local_model(MODEL_PATH)
    except Exception as error:
        print(f"[Embedding] Local Qwen model was not loaded: {error}")

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


def index_document(document_id: str) -> int:
    """Build both P3 indexes after a successful extraction."""
    if dense_index is None or not dense_index.model_ready:
        return 0
    dense_index.index_document(document_id)
    return bm25_index.index_document(document_id)

ingestion_service = DocumentIngestionService(
    DATA_ROOT,
    metadata_store=metadata_store,
)
