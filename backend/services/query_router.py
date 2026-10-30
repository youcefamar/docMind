"""Tier 1 routing and query reformulation powered by NVIDIA Nemotron Nano.

Routes user questions to expanded retrieval terms and appropriate category
filters before execution against FAISS and BM25, minimizing Tier 2 reasoning bloat.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from models.contracts import QueryRoutingResult
from services.settings import settings

logger = logging.getLogger("docmind.router")

_JSON_BLOCK_PATTERN = re.compile(r"\{[^{}]*\}", re.DOTALL)


class QueryRouterService:
    """Fast Tier 1 inference engine utilizing NVIDIA Nemotron Nano on Nebius."""

    def __init__(self, llm_service: Optional[Any] = None) -> None:
        self.llm_service = llm_service
        self.fast_model = os.getenv("NEBIUS_FAST_MODEL", settings.nebius_fast_model).strip()
        self.routing_enabled = os.getenv("DOCMIND_QUERY_ROUTING_ENABLED", "true").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    @property
    def is_ready(self) -> bool:
        client = getattr(self.llm_service, "nebius_client", None)
        return bool(self.routing_enabled and client is not None)

    def route_query(
        self,
        question: str,
        current_category: Optional[str] = "All",
        valid_categories: tuple[str, ...] = (),
    ) -> QueryRoutingResult:
        """Reformulate query and classify category using Nemotron Nano."""
        started_at = time.perf_counter()
        normalized_category = current_category if current_category and current_category != "All" else None

        if not self.routing_enabled or not question or not question.strip():
            return QueryRoutingResult(
                original_query=question or "",
                refined_query=question or "",
                category=current_category,
                router_applied=False,
                elapsed_ms=0.0,
                model="passthrough",
            )

        client = getattr(self.llm_service, "nebius_client", None)
        if client is None:
            elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
            return QueryRoutingResult(
                original_query=question,
                refined_query=question,
                category=current_category,
                router_applied=False,
                elapsed_ms=elapsed_ms,
                model="extractive-passthrough",
            )

        categories_hint = ", ".join(valid_categories or settings.categories)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are DocMind's Tier 1 Query Routing Engine. "
                    "Analyze the user question to optimize retrieval against FAISS vector and BM25 lexical indexes.\n"
                    "Output a single JSON object with:\n"
                    '1. "search_terms": concise expanded keywords (synonyms, technical terms, key entities) for search.\n'
                    f'2. "category": the single best category match from [{categories_hint}], or "All" if ambiguous.\n'
                    'Output format: {"search_terms": "...", "category": "..."}\n'
                    "Do not include any explanation or extra text."
                ),
            },
            {
                "role": "user",
                "content": f"User question: {question}",
            },
        ]

        try:
            response = client.chat.completions.create(
                model=self.fast_model,
                messages=messages,
                temperature=0.0,
                max_tokens=int(os.getenv("DOCMIND_ROUTER_MAX_TOKENS", "100")),
            )
            raw_content = (response.choices[0].message.content or "").strip()
            usage = getattr(response, "usage", None)
            prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
            completion_tokens = getattr(usage, "completion_tokens", None) if usage else None
            elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)

            parsed = self._extract_json(raw_content)
            refined_query = str(parsed.get("search_terms") or "").strip() if parsed else ""
            if not refined_query:
                refined_query = question

            predicted_category = str(parsed.get("category") or "").strip() if parsed else ""
            effective_category = self._resolve_category(
                normalized_category or predicted_category,
                valid_categories=valid_categories or settings.categories,
            )

            logger.info(
                "[ROUTER] [Tier 1 Nemotron Nano] reformulated in %.1fms (tokens=%s): '%s' -> '%s' [cat=%s]",
                elapsed_ms,
                (prompt_tokens or 0) + (completion_tokens or 0),
                question,
                refined_query,
                effective_category,
            )

            return QueryRoutingResult(
                original_query=question,
                refined_query=refined_query,
                category=effective_category,
                router_applied=True,
                elapsed_ms=elapsed_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                model=self.fast_model,
            )
        except Exception as error:
            elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
            logger.warning("[ROUTER] Tier 1 routing error: %s; falling back to original query", error)
            return QueryRoutingResult(
                original_query=question,
                refined_query=question,
                category=current_category,
                router_applied=False,
                elapsed_ms=elapsed_ms,
                model="fallback-on-error",
            )

    def filter_and_rerank_chunks(
        self,
        question: str,
        chunks: List[Dict[str, Any]],
        target_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Filter retrieved chunks down to high-density context blocks."""
        if not chunks or len(chunks) <= target_k:
            return chunks

        # Sort candidate chunks by similarity descending and preserve top target_k
        sorted_chunks = sorted(
            chunks,
            key=lambda item: float(item.get("similarity", 0.0)),
            reverse=True,
        )
        return sorted_chunks[:target_k]

    @staticmethod
    def _extract_json(text: str) -> Optional[dict]:
        """Safely extract JSON object from model output."""
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        match = _JSON_BLOCK_PATTERN.search(text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None

    @staticmethod
    def _resolve_category(
        candidate: Optional[str],
        valid_categories: tuple[str, ...],
    ) -> str:
        """Resolve a predicted category against the whitelist."""
        if not candidate or candidate.casefold() in {"all", "none", "unknown"}:
            return "All"
        candidate_fold = candidate.casefold()
        for cat in valid_categories:
            if cat.casefold() == candidate_fold:
                return cat
        return "All"
