import logging
import os
import time
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from models.contracts import RetrievalProfile
from pydantic import BaseModel, Field
from services.embedder import EmbeddingService
from services.llm import citation_is_supported, validate_citations
from services.retriever import VectorStoreService
from services.runtime import dense_index, llm_service, quality_retriever, query_router
from services.settings import settings

router = APIRouter(prefix="/api", tags=["Chat"])
logger = logging.getLogger("docmind.chat")


class ChatMessage(BaseModel):
    sender: str
    content: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, json_schema_extra={"example": "What is the remote work policy?"})
    category: Optional[str] = Field("All", description="Configured category filter or All")
    chat_history: Optional[List[Dict[str, str]]] = Field(
        default=[], description="Multi-turn conversation history"
    )
    retrieval_profile: RetrievalProfile = RetrievalProfile.FAST


class SourceResponse(BaseModel):
    doc_id: str
    chunk_id: Optional[str] = None
    filename: str
    category: str
    page_number: int
    total_pages: int
    excerpt: str
    similarity: float
    rank: Optional[int] = None
    location_type: str = "page"
    location_value: str = "1"


class AskResponse(BaseModel):
    answer: str
    confidence_score: float
    confidence_label: str
    sources: List[SourceResponse]
    citations: List[Dict[str, object]] = Field(default_factory=list)
    retrieval_profile: RetrievalProfile
    telemetry: Optional[Dict[str, object]] = None


embedder_service = EmbeddingService()
retriever_service = VectorStoreService()


def _dense_sources(question: str, category: Optional[str], top_k: int) -> list[dict]:
    if not dense_index or not dense_index.model_ready:
        return []
    results = dense_index.search(question, category=category, top_k=top_k)
    sources = []
    for result in results:
        document = dense_index.metadata_store.get_document(result.document_id)
        if not document:
            continue
        page_number = int(result.location_value) if result.location_type == "page" else 1
        sources.append(
            {
                "doc_id": result.document_id,
                "chunk_id": result.chunk_id,
                "filename": result.filename,
                "category": result.category,
                "page_number": page_number,
                "total_pages": document.total_pages,
                "excerpt": result.text,
                "similarity": round(result.score, 3),
                "rank": result.rank,
                "location_type": result.location_type,
                "location_value": result.location_value,
            }
        )
    return sources


@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    started_at = time.perf_counter()
    log_question = os.getenv("DOCMIND_LOG_QUERIES", "false").lower() == "true"
    question_marker = request.question if log_question else "<hidden>"
    logger.info(
        "[ASK] received profile=%s category=%s question=%s",
        request.retrieval_profile.value,
        request.category,
        question_marker,
    )
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if request.retrieval_profile is RetrievalProfile.QUALITY and (
        quality_retriever is None or not quality_retriever.ready
    ):
        raise HTTPException(
            status_code=501,
            detail="Quality retrieval requires a ready Qwen dense index and BM25 index.",
        )

    try:
        routing_result = query_router.route_query(
            question=request.question,
            current_category=request.category,
            valid_categories=settings.categories,
        )
        search_query = routing_result.refined_query or request.question
        effective_category = (
            request.category
            if request.category and request.category != "All"
            else (routing_result.category or "All")
        )

        retrieval_started_at = time.perf_counter()
        if request.retrieval_profile is RetrievalProfile.QUALITY:
            quality_results = quality_retriever.search(
                search_query,
                category=effective_category,
                final_k=settings.quality_final_k,
                candidate_k=settings.quality_candidate_k,
            )
            sources = []
            for result in quality_results:
                document = quality_retriever.dense_index.metadata_store.get_document(
                    result.document_id
                )
                if not document:
                    continue
                sources.append(
                    {
                        "doc_id": result.document_id,
                        "chunk_id": result.chunk_id,
                        "filename": result.filename,
                        "category": result.category,
                        "page_number": int(result.location_value)
                        if result.location_type == "page"
                        else 1,
                        "total_pages": document.total_pages,
                        "excerpt": result.text,
                        "similarity": round(result.score, 3),
                        "rank": result.rank,
                        "location_type": result.location_type,
                        "location_value": result.location_value,
                    }
                )
        else:
            sources = _dense_sources(
                search_query,
                effective_category,
                top_k=settings.fast_top_k,
            )
        if not sources and request.retrieval_profile is RetrievalProfile.FAST:
            # Transitional fallback for documents indexed by the old pgvector path.
            query_embeddings = embedder_service.generate_embeddings([search_query])
            sources = retriever_service.search(
                query_embedding=query_embeddings,
                category=effective_category,
                top_k=settings.fast_top_k,
            )
        retrieval_ms = (time.perf_counter() - retrieval_started_at) * 1000

        target_k = settings.quality_final_k if request.retrieval_profile is RetrievalProfile.QUALITY else settings.fast_top_k
        sources = query_router.filter_and_rerank_chunks(
            question=request.question,
            chunks=sources,
            target_k=target_k,
        )

        logger.info(
            "[ASK] retrieval profile=%s sources=%d elapsed_ms=%.1f dense_ready=%s router_applied=%s",
            request.retrieval_profile.value,
            len(sources),
            retrieval_ms,
            bool(dense_index and dense_index.model_ready),
            routing_result.router_applied,
        )
        for source in sources:
            logger.info(
                "[ASK] source rank=%s file=%s location=%s:%s score=%.3f",
                source.get("rank"),
                source.get("filename"),
                source.get("location_type", "page"),
                source.get("location_value", source.get("page_number", "1")),
                float(source.get("similarity", 0.0)),
            )

        generation_started_at = time.perf_counter()
        answer, confidence_score, confidence_label = llm_service.generate_answer(
            question=request.question,
            sources=sources,
            chat_history=request.chat_history,
            retrieval_profile=request.retrieval_profile.value,
        )
        generation_ms = (time.perf_counter() - generation_started_at) * 1000
        citations = [
            {
                "source_id": citation.source_id,
                "chunk_id": citation.chunk_id,
                "doc_id": citation.document_id,
                "filename": citation.filename,
                "location_type": citation.location_type,
                "location_value": citation.location_value,
                "excerpt": citation.excerpt,
                "supported": citation_is_supported(answer, citation),
            }
            for citation in validate_citations(answer, sources)
        ]
        total_ms = (time.perf_counter() - started_at) * 1000

        gen_stats = getattr(llm_service, "last_generation_stats", {})
        tier2_prompt_tokens = gen_stats.get("prompt_tokens")
        tier2_completion_tokens = gen_stats.get("completion_tokens")
        tier2_total_tokens = gen_stats.get("total_tokens")
        tier2_tokens_per_second = gen_stats.get("tokens_per_second")
        tier1_tokens = (routing_result.prompt_tokens or 0) + (routing_result.completion_tokens or 0)
        estimated_credits_saved = 72.0 if routing_result.router_applied else 0.0

        telemetry: Dict[str, object] = {
            "tier1_model": routing_result.model or getattr(query_router, "fast_model", "none"),
            "tier1_applied": routing_result.router_applied,
            "tier1_elapsed_ms": routing_result.elapsed_ms,
            "tier1_tokens": tier1_tokens,
            "tier1_refined_query": routing_result.refined_query,
            "tier2_model": getattr(llm_service, "model_name", "unknown"),
            "tier2_prompt_tokens": tier2_prompt_tokens,
            "tier2_completion_tokens": tier2_completion_tokens,
            "tier2_total_tokens": tier2_total_tokens,
            "tier2_tokens_per_second": tier2_tokens_per_second,
            "generation_ms": round(generation_ms, 2),
            "retrieval_ms": round(retrieval_ms, 2),
            "total_ms": round(total_ms, 2),
            "estimated_credits_saved_percent": estimated_credits_saved,
        }

        logger.info(
            "[ASK] [Dual-Nemotron] completed sources=%d citations=%d confidence=%s llm_backend=%s "
            "retrieval_ms=%.1f generation_ms=%.1f total_ms=%.1f | Tier 1: %s (%.1fms) -> Tier 2: %s (%s tokens, %s tps)",
            len(sources),
            len(citations),
            confidence_label,
            getattr(llm_service, "backend", "unknown"),
            retrieval_ms,
            generation_ms,
            total_ms,
            telemetry["tier1_model"],
            routing_result.elapsed_ms,
            telemetry["tier2_model"],
            tier2_completion_tokens,
            tier2_tokens_per_second,
        )

        return AskResponse(
            answer=answer,
            confidence_score=confidence_score,
            confidence_label=confidence_label,
            sources=[SourceResponse(**source) for source in sources],
            citations=citations,
            retrieval_profile=request.retrieval_profile,
            telemetry=telemetry,
        )
    except Exception as error:
        logger.exception("[ASK] failed after %.1f ms: %s", (time.perf_counter() - started_at) * 1000, error)
        raise HTTPException(status_code=500, detail=f"Error processing question: {error}") from error
