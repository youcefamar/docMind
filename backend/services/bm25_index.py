"""Persistent lightweight BM25 lexical retrieval over SQLite chunks."""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Optional

from models.contracts import ChunkRecord
from services.metadata_store import MetadataStore


class BM25IndexError(RuntimeError):
    """Raised when the lexical index cannot be loaded or built."""


class BM25IndexService:
    """Persist a multilingual-safe token index and execute BM25 scoring."""

    TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)

    def __init__(
        self,
        index_root: str | Path,
        metadata_store: MetadataStore,
        k1: float = 1.5,
        b: float = 0.75,
    ):
        self.index_root = Path(index_root)
        self.index_root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_root / "bm25.json"
        self.metadata_store = metadata_store
        self.k1 = k1
        self.b = b
        self.chunk_ids: list[str] = []
        self.document_lengths: list[int] = []
        self.postings: dict[str, list[list[int]]] = {}
        self.average_length = 0.0
        self._load()

    @classmethod
    def tokenize(cls, text: str) -> list[str]:
        return [token.casefold() for token in cls.TOKEN_PATTERN.findall(text)]

    @property
    def ready(self) -> bool:
        return bool(self.chunk_ids)

    def _load(self) -> None:
        if not self.index_path.is_file():
            return
        try:
            payload = json.loads(self.index_path.read_text(encoding="utf-8"))
            self.chunk_ids = payload["chunk_ids"]
            self.document_lengths = payload["document_lengths"]
            self.postings = payload["postings"]
            self.average_length = float(payload["average_length"])
            if len(self.chunk_ids) != len(self.document_lengths):
                self.chunk_ids = []
                self.document_lengths = []
                self.postings = {}
        except (OSError, ValueError, KeyError, TypeError):
            self.chunk_ids = []
            self.document_lengths = []
            self.postings = {}

    def rebuild(self, chunks: list[ChunkRecord]) -> int:
        self.chunk_ids = [chunk.id for chunk in chunks]
        self.document_lengths = []
        self.postings = {}
        for index, chunk in enumerate(chunks):
            tokens = self.tokenize(chunk.text)
            self.document_lengths.append(len(tokens))
            term_frequencies: dict[str, int] = {}
            for token in tokens:
                term_frequencies[token] = term_frequencies.get(token, 0) + 1
            for token, frequency in term_frequencies.items():
                self.postings.setdefault(token, []).append([index, frequency])
        self.average_length = sum(self.document_lengths) / len(self.document_lengths) if chunks else 0.0
        self._persist()
        return len(chunks)

    def rebuild_from_store(self) -> int:
        return self.rebuild(self.metadata_store.list_chunks())

    def index_document(self, document_id: str) -> int:
        del document_id
        return self.rebuild_from_store()

    def _persist(self) -> None:
        temporary_path = self.index_path.with_suffix(".json.tmp")
        temporary_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "k1": self.k1,
                    "b": self.b,
                    "chunk_ids": self.chunk_ids,
                    "document_lengths": self.document_lengths,
                    "average_length": self.average_length,
                    "postings": self.postings,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        os.replace(temporary_path, self.index_path)

    def search_ids(
        self,
        question: str,
        category: Optional[str] = None,
        top_k: int = 30,
    ) -> list[tuple[str, float]]:
        if not self.ready or top_k <= 0:
            return []

        query_terms = self.tokenize(question)
        scores = [0.0] * len(self.chunk_ids)
        total_documents = len(self.chunk_ids)
        for term in query_terms:
            postings = self.postings.get(term, [])
            if not postings:
                continue
            document_frequency = len(postings)
            idf = math.log(1.0 + (total_documents - document_frequency + 0.5) / (document_frequency + 0.5))
            for index, frequency in postings:
                document_length = self.document_lengths[index]
                normalization = 1.0 - self.b + self.b * document_length / (self.average_length or 1.0)
                scores[index] += idf * (frequency * (self.k1 + 1.0)) / (
                    frequency + self.k1 * normalization
                )

        ranked = sorted(
            enumerate(scores),
            key=lambda item: item[1],
            reverse=True,
        )
        results = []
        for index, score in ranked:
            if score <= 0:
                continue
            chunk = self.metadata_store.get_chunk(self.chunk_ids[index])
            if not chunk:
                continue
            document = self.metadata_store.get_document(chunk.document_id)
            if not document:
                continue
            if category and category.casefold() != "all" and document.category.casefold() != category.casefold():
                continue
            results.append((chunk.id, float(score)))
            if len(results) == top_k:
                break
        return results
