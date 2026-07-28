"""Optional local BGE reranking adapter."""

from __future__ import annotations

from typing import Any, Optional

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None


class LocalReranker:
    MODEL_NAME = "BAAI/bge-reranker-v2-m3"

    def __init__(self, model: Optional[Any] = None, model_name: str = MODEL_NAME):
        self.model = model
        self.model_name = model_name
        self.model_revision: Optional[str] = None

    @property
    def is_ready(self) -> bool:
        return self.model is not None

    def load_local_model(self, model_path: str, revision: Optional[str] = None) -> None:
        if CrossEncoder is None:
            raise RuntimeError("sentence-transformers is not installed")
        self.model = CrossEncoder(
            model_path,
            device="cpu",
            local_files_only=True,
            trust_remote_code=True,
            revision=revision,
            max_length=512,
        )
        self.model_revision = revision or model_path

    def score(self, question: str, passages: list[str]) -> list[float]:
        if not self.model:
            return []
        pairs = [[question, passage] for passage in passages]
        scores = self.model.predict(pairs, show_progress_bar=False)
        return [float(score) for score in scores]
