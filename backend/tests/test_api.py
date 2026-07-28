from pathlib import Path

from fastapi.testclient import TestClient
from main import app
from models.contracts import (
    DocumentRecord,
    DocumentStatus,
    RetrievalProfile,
    RetrievalResult,
)
from routes import chat as chat_route
from routes import documents as documents_route
from services.ingestion import DocumentIngestionService

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["app"] == "DocMind Backend API"

def test_list_documents_endpoint():
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_ask_question_empty_validation():
    response = client.post("/api/ask", json={"question": "   ", "category": "All"})
    assert response.status_code == 400


def test_upload_catalog_and_delete_use_local_ingestion(tmp_path: Path, monkeypatch):
    service = DocumentIngestionService(tmp_path / "data")
    monkeypatch.setattr(documents_route, "ingestion_service", service)

    upload = client.post(
        "/api/upload",
        files={"files": ("policy.md", b"Remote work is allowed.", "text/markdown")},
        data={"category": "HR"},
    )

    assert upload.status_code == 200
    uploaded = upload.json()[0]
    assert uploaded["status"] == "partially_indexed"
    assert uploaded["chunks_created"] == 1

    catalog = client.get("/api/docs")
    assert catalog.status_code == 200
    assert catalog.json()[0]["filename"] == "policy.md"

    duplicate = client.post(
        "/api/upload",
        files={"files": ("policy.md", b"Remote work is allowed.", "text/markdown")},
        data={"category": "HR"},
    )
    assert duplicate.status_code == 200
    assert duplicate.json()[0]["duplicate"] is True

    deleted = client.delete(f"/api/doc/{uploaded['doc_id']}")
    assert deleted.status_code == 200
    assert client.get("/api/docs").json() == []


def test_ask_uses_fast_dense_results_when_available(monkeypatch):
    class FakeMetadata:
        def get_document(self, document_id):
            now = "2026-01-01T00:00:00+00:00"
            return DocumentRecord(
                id=document_id,
                filename="policy.md",
                sha256="a" * 64,
                size_bytes=10,
                category="HR",
                status=DocumentStatus.INDEXED,
                original_path="policy.md",
                chunk_count=1,
                total_pages=1,
                created_at=now,
                updated_at=now,
            )

    class FakeDense:
        model_ready = True
        metadata_store = FakeMetadata()

        def search(self, question, category=None, top_k=5):
            return [
                RetrievalResult(
                    chunk_id="doc-1:chunk:1",
                    document_id="doc-1",
                    text="Remote work is allowed.",
                    rank=1,
                    score=0.91,
                    retrieval_profile=RetrievalProfile.FAST,
                    filename="policy.md",
                    category="HR",
                    location_type="page",
                    location_value="1",
                )
            ]

    class FakeLLM:
        def generate_answer(self, question, sources, chat_history=None):
            return "Remote work is allowed. [S1]", 0.91, "High"

    monkeypatch.setattr(chat_route, "dense_index", FakeDense())
    monkeypatch.setattr(chat_route, "llm_service", FakeLLM())

    response = client.post(
        "/api/ask",
        json={"question": "Can I work remotely?", "retrieval_profile": "fast"},
    )

    assert response.status_code == 200
    assert response.json()["retrieval_profile"] == "fast"
    assert response.json()["sources"][0]["filename"] == "policy.md"


def test_ask_uses_quality_retriever_when_available(monkeypatch):
    class FakeMetadata:
        def get_document(self, document_id):
            return DocumentRecord(
                id=document_id,
                filename="quality.md",
                sha256="b" * 64,
                size_bytes=10,
                category="HR",
                status=DocumentStatus.INDEXED,
                original_path="quality.md",
                chunk_count=1,
                total_pages=1,
                created_at="2026-01-01T00:00:00+00:00",
                updated_at="2026-01-01T00:00:00+00:00",
            )

    class FakeQuality:
        ready = True
        dense_index = type("Dense", (), {"metadata_store": FakeMetadata()})()

        def search(self, question, category=None, final_k=5):
            return [
                RetrievalResult(
                    chunk_id="doc-quality:chunk:1",
                    document_id="doc-quality",
                    text="Quality evidence.",
                    rank=1,
                    score=0.88,
                    retrieval_profile=RetrievalProfile.QUALITY,
                    filename="quality.md",
                    category="HR",
                    location_type="page",
                    location_value="1",
                )
            ]

    class FakeLLM:
        def generate_answer(self, question, sources, chat_history=None):
            return "Quality evidence. [S1]", 0.88, "High"

    monkeypatch.setattr(chat_route, "quality_retriever", FakeQuality())
    monkeypatch.setattr(chat_route, "llm_service", FakeLLM())

    response = client.post(
        "/api/ask",
        json={"question": "What is the evidence?", "retrieval_profile": "quality"},
    )

    assert response.status_code == 200
    assert response.json()["retrieval_profile"] == "quality"
    assert response.json()["sources"][0]["filename"] == "quality.md"
