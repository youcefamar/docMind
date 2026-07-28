"""Hybrid BM25+dense retrieval with RRF and optional reranking."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Optional

from models.contracts import RetrievalProfile, RetrievalResult
from services.bm25_index import BM25IndexService
from services.dense_index import DenseIndexService
from services.reranker import LocalReranker


def reciprocal_rank_fusion(
    rankings: list[list[tuple[str, float]]],
    rrf_k: int = 60,
    top_k: int = 30,
) -> list[tuple[str, float]]:
    """Fuse ranked chunk IDs without comparing incompatible score scales."""
    fused_scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, (chunk_id, _score) in enumerate(ranking, start=1):
            fused_scores[chunk_id] += 1.0 / (rrf_k + rank)
    return sorted(fused_scores.items(), key=lambda item: item[1], reverse=True)[:top_k]


class QualityRetriever:
    def __init__(
        self,
        dense_index: DenseIndexService,
        bm25_index: BM25IndexService,
        reranker: Optional[LocalReranker] = None,
    ):
        self.dense_index = dense_index
        self.bm25_index = bm25_index
        self.reranker = reranker

    @property
    def ready(self) -> bool:
        return self.dense_index.model_ready and self.dense_index.ready and self.bm25_index.ready

    @property
    def reranker_ready(self) -> bool:
        return bool(self.reranker and self.reranker.is_ready)

    def search(
        self,
        question: str,
        category: Optional[str] = None,
        final_k: int = 5,
        candidate_k: int = 30,
    ) -> list[RetrievalResult]:
        if not self.ready or final_k <= 0:
            return []

        dense = self.dense_index.search(question, category=category, top_k=candidate_k)
        dense_ranking = [(result.chunk_id, result.score) for result in dense]
        lexical_ranking = self.bm25_index.search_ids(question, category=category, top_k=candidate_k)
        fused = reciprocal_rank_fusion([dense_ranking, lexical_ranking], top_k=candidate_k)

        candidates: list[tuple[str, float, Any]] = []
        for chunk_id, fusion_score in fused:
            chunk = self.dense_index.metadata_store.get_chunk(chunk_id)
            if not chunk:
                continue
            document = self.dense_index.metadata_store.get_document(chunk.document_id)
            if not document:
                continue
            candidates.append((chunk_id, fusion_score, (chunk, document)))

        rerank_scores: dict[str, float] = {}
        if self.reranker_ready:
            scores = self.reranker.score(question, [item[2][0].text for item in candidates])
            rerank_scores = {
                candidate[0]: score for candidate, score in zip(candidates, scores)
            }
            candidates.sort(key=lambda item: rerank_scores.get(item[0], float("-inf")), reverse=True)

        results = []
        for rank, (chunk_id, fusion_score, (chunk, document)) in enumerate(candidates[:final_k], start=1):
            results.append(
                RetrievalResult(
                    chunk_id=chunk_id,
                    document_id=document.id,
                    text=chunk.text,
                    rank=rank,
                    score=rerank_scores.get(chunk_id, fusion_score),
                    retrieval_profile=RetrievalProfile.QUALITY,
                    filename=document.filename,
                    category=document.category,
                    location_type=chunk.location_type,
                    location_value=chunk.location_value,
                )
            )
        return results
