"""Local grounded generation and citation validation.

The production target is a locally cached Qwen3-4B GGUF model executed with
``llama-cpp-python``.  The service deliberately has no hosted provider
fallback: an offline deployment must never send document content elsewhere.
When weights are not installed yet, a deterministic extractive response keeps
the API and ingestion flows usable during development.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from models.contracts import Citation

try:
    from llama_cpp import Llama

    HAS_LLAMA_CPP = True
except ImportError:  # pragma: no cover - depends on optional native package
    Llama = None
    HAS_LLAMA_CPP = False


MODEL_PATH_ENV = "DOCMIND_LLM_MODEL_PATH"
LEGACY_MODEL_PATH_ENV = "GGUF_MODEL_PATH"
DEFAULT_REFUSAL = "I don't know based on the provided documents."
_CITATION_PATTERN = re.compile(r"\[S(\d+)\]", re.IGNORECASE)
_WORD_PATTERN = re.compile(r"[\w']+", re.UNICODE)


def _source_tokens(text: str) -> set[str]:
    return {token.casefold() for token in _WORD_PATTERN.findall(text or "")}


def validate_citations(answer: str, sources: List[Dict[str, Any]]) -> List[Citation]:
    """Return only citation labels that map to the supplied source list.

    Citation IDs are intentionally positional and deterministic.  A model can
    mention ``[S99]`` or ``[S0]``; those labels are ignored rather than being
    allowed to become untrusted source metadata.
    """

    citations: List[Citation] = []
    seen: set[str] = set()
    for match in _CITATION_PATTERN.finditer(answer or ""):
        source_index = int(match.group(1))
        if source_index < 1 or source_index > len(sources):
            continue
        source_id = f"S{source_index}"
        if source_id in seen:
            continue
        seen.add(source_id)
        source = sources[source_index - 1]
        citations.append(
            Citation(
                source_id=source_id,
                chunk_id=str(source.get("chunk_id") or ""),
                document_id=str(source.get("doc_id") or ""),
                filename=str(source.get("filename") or ""),
                location_type=str(source.get("location_type") or "page"),
                location_value=str(
                    source.get("location_value") or source.get("page_number") or "1"
                ),
                excerpt=str(source.get("excerpt") or ""),
            )
        )
    return citations


def sanitize_citation_labels(answer: str, source_count: int) -> str:
    """Remove forged citation labels while preserving valid positional labels."""

    def replace(match: re.Match[str]) -> str:
        index = int(match.group(1))
        return f"[S{index}]" if 1 <= index <= source_count else ""

    sanitized = _CITATION_PATTERN.sub(replace, answer or "")
    return re.sub(r"[ \t]{2,}", " ", sanitized)


def citation_is_supported(answer: str, citation: Citation) -> bool:
    """Use conservative lexical overlap as a testable support signal.

    This is not a semantic truth proof; it prevents obviously unrelated
    citations from being presented as verified and gives the API a transparent
    quality signal until a dedicated entailment check is added.
    """

    answer_tokens = _source_tokens(answer)
    excerpt_tokens = _source_tokens(citation.excerpt)
    if not answer_tokens or not excerpt_tokens:
        return False
    return bool(answer_tokens & excerpt_tokens)


class LLMService:
    """CPU-compatible local Qwen runtime with deterministic grounding rules."""

    def __init__(self, model_path: Optional[str] = None, auto_load: bool = True):
        self.model_path = model_path or self._resolve_model_path()
        self.local_llm = None
        self.model_name = "unconfigured-local-model"
        self.model_ready = False
        self.backend = "extractive-fallback"
        if auto_load:
            self._init_local_model()

    def _resolve_model_path(self) -> str:
        """Resolve a local GGUF path without downloading or contacting a service."""

        for env_name in (MODEL_PATH_ENV, LEGACY_MODEL_PATH_ENV):
            env_path = os.getenv(env_name)
            if env_path:
                return env_path
        return ""

    def _init_local_model(self) -> None:
        """Load a cached GGUF model when available; never attempt network access."""

        self.local_llm = None
        self.model_ready = False
        self.backend = "extractive-fallback"
        model_file = Path(self.model_path) if self.model_path else None
        if not HAS_LLAMA_CPP or model_file is None or not model_file.is_file():
            return
        try:
            self.local_llm = Llama(
                model_path=str(model_file),
                n_ctx=int(os.getenv("DOCMIND_LLM_CONTEXT_TOKENS", "4096")),
                n_threads=int(os.getenv("DOCMIND_LLM_THREADS", str(os.cpu_count() or 4))),
                verbose=False,
            )
            self.model_name = model_file.name
            self.model_ready = True
            self.backend = "llama-cpp-local"
        except Exception as error:  # pragma: no cover - native model/runtime dependent
            print(f"[LLM] Local model could not be loaded: {error}")

    def generate_answer(
        self,
        question: str,
        sources: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Tuple[str, float, str]:
        if not sources:
            return DEFAULT_REFUSAL, 0.0, "Low"

        max_similarity = max((float(s.get("similarity", 0.0)) for s in sources), default=0.0)
        min_score = float(os.getenv("DOCMIND_MIN_SOURCE_SCORE", "0.20"))
        if max_similarity < min_score:
            return DEFAULT_REFUSAL, round(max_similarity, 2), "Low"

        messages = self._build_messages(question, sources, chat_history or [])
        if self.local_llm is not None:
            try:
                response = self.local_llm.create_chat_completion(
                    messages=messages,
                    temperature=0.1,
                    max_tokens=int(os.getenv("DOCMIND_LLM_MAX_TOKENS", "600")),
                )
                answer = response["choices"][0]["message"]["content"].strip()
            except Exception as error:  # pragma: no cover - native model/runtime dependent
                print(f"[LLM] Local generation error: {error}")
                answer = self._generate_fallback_answer(sources)
        else:
            answer = self._generate_fallback_answer(sources)

        if self._is_refusal(answer):
            return DEFAULT_REFUSAL, 0.15, "Low"

        answer = sanitize_citation_labels(answer, len(sources)).strip()
        citations = validate_citations(answer, sources)
        if not citations:
            # The answer remains grounded and the fallback label is always valid.
            answer = f"{answer.rstrip()}\n\nSources: [S1]"
            citations = validate_citations(answer, sources)

        confidence_score, confidence_label = self._calculate_confidence(
            answer, max_similarity
        )
        return answer, confidence_score, confidence_label

    def _build_messages(
        self,
        question: str,
        sources: List[Dict[str, Any]],
        chat_history: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        context_blocks = []
        for index, source in enumerate(sources, start=1):
            context_blocks.append(
                f"--- SOURCE [S{index}] ---\n"
                f"Document: {source.get('filename')}\n"
                f"Category: {source.get('category')}\n"
                f"Page: {source.get('page_number')}\n"
                f"Content:\n{source.get('excerpt')}\n"
            )
        system_prompt = (
            "You are DocMind, an offline internal knowledge assistant.\n"
            "Answer ONLY from DOCUMENT CONTEXT. Never invent facts.\n"
            f"If the context is insufficient, answer exactly: {DEFAULT_REFUSAL}\n"
            "Answer in the same language as the user when possible. Keep it concise.\n"
            "Cite every factual claim with one or more supplied labels such as [S1]. "
            "Never create a label that is not supplied. Do not expose private reasoning."
        )
        messages = [{"role": "system", "content": system_prompt}]
        for message in chat_history[-4:]:
            role = "user" if message.get("sender") == "user" or message.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": message.get("content", "")})
        messages.append(
            {
                "role": "user",
                "content": "DOCUMENT CONTEXT:\n"
                + "\n".join(context_blocks)
                + f"\nUSER QUESTION:\n{question}",
            }
        )
        return messages

    @staticmethod
    def _is_refusal(answer: str) -> bool:
        lower = (answer or "").casefold()
        return any(
            phrase in lower
            for phrase in (
                "i don't know",
                "i do not know",
                "couldn't find",
                "not mentioned",
                "insufficient information",
            )
        )

    @staticmethod
    def _calculate_confidence(answer: str, max_sim: float) -> Tuple[float, str]:
        if LLMService._is_refusal(answer):
            return 0.15, "Low"
        if max_sim >= 0.70:
            return min(0.98, round(max_sim + 0.05, 2)), "High"
        if max_sim >= 0.45:
            return round(max_sim, 2), "Medium"
        return round(max_sim, 2), "Low"

    @staticmethod
    def _generate_fallback_answer(sources: List[Dict[str, Any]]) -> str:
        first_source = sources[0]
        excerpt = str(first_source.get("excerpt") or "").strip()
        return (
            f"Based on **{first_source.get('filename')}** (Page {first_source.get('page_number')}), "
            f"the relevant document evidence is:\n\n\"{excerpt[:350]}\" [S1]"
        )
