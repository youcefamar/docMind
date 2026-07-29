from fastapi import APIRouter
from services.runtime import (
    bm25_index,
    dense_index,
    embedding_service,
    indexing_queue,
    metadata_store,
    quality_retriever,
    reranker,
)

router = APIRouter(prefix="/api/runtime", tags=["Runtime"])


@router.get("/status")
async def runtime_status() -> dict:
    """Expose safe readiness state for the workspace UI and local diagnostics."""

    from routes.chat import llm_service

    documents = metadata_store.list_documents()
    return {
        "embedding_ready": embedding_service.is_ready,
        "dense_index_ready": bool(dense_index and dense_index.ready),
        "bm25_index_ready": bm25_index.ready,
        "reranker_ready": reranker.is_ready,
        "quality_ready": bool(quality_retriever and quality_retriever.ready),
        "llm_ready": llm_service.model_ready,
        "llm_backend": llm_service.backend,
        "llm_model": llm_service.model_name,
        "document_count": len(documents),
        "indexed_document_count": sum(document.status.value == "indexed" for document in documents),
        "indexing_queue": indexing_queue.status(),
    }
