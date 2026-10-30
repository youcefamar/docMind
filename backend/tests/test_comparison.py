from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from models.contracts import ChunkRecord, DocumentRecord, DocumentStatus
from services.comparison import DocumentComparisonService


def _fake_doc(doc_id: str, filename: str) -> DocumentRecord:
    now = datetime.now(timezone.utc)
    return DocumentRecord(
        id=doc_id,
        filename=filename,
        sha256="c" * 64 if doc_id == "doc-1" else "d" * 64,
        size_bytes=100,
        category="HR",
        status=DocumentStatus.INDEXED,
        total_pages=2,
        chunk_count=2,
        created_at=now,
        updated_at=now,
    )


def _fake_chunk(chunk_id: str, doc_id: str, text: str) -> ChunkRecord:
    return ChunkRecord(
        id=chunk_id,
        document_id=doc_id,
        block_id="block-1",
        text=text,
        token_count=10,
        chunk_index=0,
        location_type="page",
        location_value="1",
    )


class FakeStore:
    def __init__(self, docs=None, chunks=None):
        self.docs = docs or {}
        self.chunks = chunks or {}

    def get_document(self, doc_id: str):
        return self.docs.get(doc_id)

    def get_chunks(self, doc_id: str):
        return self.chunks.get(doc_id, [])


def test_comparison_requires_at_least_two_documents():
    service = DocumentComparisonService(FakeStore(), type("LLM", (), {"nebius_client": None})())

    with pytest.raises(HTTPException) as exc_info:
        service.compare_documents(["doc-1"])
    assert exc_info.value.status_code == 400


def test_comparison_rejects_missing_document():
    store = FakeStore(docs={"doc-1": _fake_doc("doc-1", "doc1.pdf")})
    service = DocumentComparisonService(store, type("LLM", (), {"nebius_client": None})())

    with pytest.raises(HTTPException) as exc_info:
        service.compare_documents(["doc-1", "non-existent"])
    assert exc_info.value.status_code == 404
    assert "non-existent" in exc_info.value.detail


def test_comparison_deterministic_fallback():
    docs = {
        "doc-1": _fake_doc("doc-1", "Policy2025.pdf"),
        "doc-2": _fake_doc("doc-2", "Policy2026.pdf"),
    }
    chunks = {
        "doc-1": [_fake_chunk("c1", "doc-1", "Remote work allowed 2 days.")],
        "doc-2": [_fake_chunk("c2", "doc-2", "Remote work allowed 4 days.")],
    }
    store = FakeStore(docs, chunks)
    llm = type("LLM", (), {"nebius_client": None, "model_name": "extractive-model"})()
    service = DocumentComparisonService(store, llm)

    response = service.compare_documents(["doc-1", "doc-2"], focus_aspect="Remote work")

    assert response.focus_aspect == "Remote work"
    assert len(response.documents) == 2
    assert "Policy2025.pdf" in response.comparison_markdown
    assert "Policy2026.pdf" in response.comparison_markdown
    assert "Key Differences Matrix" in response.comparison_markdown


def test_comparison_with_mocked_nemotron_client():
    class FakeUsage:
        prompt_tokens = 250
        completion_tokens = 110
        total_tokens = 360

    class FakeMessage:
        content = (
            "<think>evaluating differences</think>\n"
            "# Cross-Document Comparative Report\n\n"
            "## 1. Executive Summary\n"
            "Significant expansion of remote work allowances.\n\n"
            "## 2. Key Differences Matrix\n"
            "| Dimension | Policy 2025 | Policy 2026 | Impact |\n"
            "|---|---|---|---|\n"
            "| Remote Days | 2 days | 4 days | +100% flexibility |"
        )

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]
        usage = FakeUsage()

    class FakeOpenAI:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return FakeResponse()

    docs = {
        "doc-1": _fake_doc("doc-1", "Policy2025.pdf"),
        "doc-2": _fake_doc("doc-2", "Policy2026.pdf"),
    }
    chunks = {
        "doc-1": [_fake_chunk("c1", "doc-1", "Remote work allowed 2 days.")],
        "doc-2": [_fake_chunk("c2", "doc-2", "Remote work allowed 4 days.")],
    }
    store = FakeStore(docs, chunks)
    llm = type(
        "LLM",
        (),
        {
            "nebius_client": FakeOpenAI(),
            "nebius_reasoning_model": "nvidia/nemotron-3-ultra",
            "model_name": "nvidia/nemotron-3-ultra",
        },
    )()

    service = DocumentComparisonService(store, llm)
    response = service.compare_documents(["doc-1", "doc-2"])

    assert "Remote Days" in response.comparison_markdown
    assert "think" not in response.comparison_markdown
    assert response.telemetry is not None
    assert response.telemetry["model"] == "nvidia/nemotron-3-ultra"
    assert response.telemetry["prompt_tokens"] == 250
    assert response.telemetry["completion_tokens"] == 110
    assert response.telemetry["tokens_per_second"] is not None
