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
from routes import models as models_route
from routes import sources as sources_route
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


def test_public_config_exposes_dynamic_ui_options():
    response = client.get("/api/config/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["default_category"] in payload["categories"]
    assert "pdf" in {extension.lstrip(".") for extension in payload["supported_extensions"]}
    assert payload["retrieval_defaults"]["fast_top_k"] > 0


def test_runtime_status_exposes_safe_readiness_state():
    response = client.get("/api/runtime/status")

    assert response.status_code == 200
    payload = response.json()
    assert "embedding_ready" in payload
    assert "llm_ready" in payload
    assert "quality_ready" in payload


def test_source_sync_status_exposes_managed_folder_state():
    response = client.get("/api/sources/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"idle", "queued", "syncing", "completed", "failed"}
    assert "source_dir" in payload


def test_source_sync_endpoint_queues_without_blocking(monkeypatch):
    class FakeSync:
        def start_background(self):
            return True

        def status(self):
            return {"status": "queued", "source_dir": "C:/knowledge"}

    monkeypatch.setattr(sources_route, "folder_sync_service", FakeSync())
    response = client.post("/api/sources/sync")

    assert response.status_code == 202
    assert response.json()["queued"] is True
    assert response.json()["status"]["status"] == "queued"

def test_ask_question_empty_validation():
    response = client.post("/api/ask", json={"question": "   ", "category": "All"})
    assert response.status_code == 400


def test_model_registry_exposes_local_qwen_entry():
    response = client.get("/api/models/")

    assert response.status_code == 200
    assert response.json()["models"][0]["id"] == "qwen3-4b-q4"
    assert response.json()["models"][0]["repo_id"] == "Qwen/Qwen3-4B-GGUF"


def test_model_download_is_queued_without_network(monkeypatch):
    monkeypatch.setattr(models_route, "_download_task", lambda model: None)

    response = client.post("/api/models/download", json={"model_id": "qwen3-4b-q4"})

    assert response.status_code == 200
    assert response.json()["model_id"] == "qwen3-4b-q4"
    assert response.json()["status"] in {"queued", "completed"}


def test_upload_catalog_and_delete_use_local_ingestion(tmp_path: Path, monkeypatch):
    service = DocumentIngestionService(tmp_path / "data")
    monkeypatch.setattr(documents_route, "ingestion_service", service)
    # Keep this lifecycle test independent of whichever local embedding model
    # happens to be installed on the developer machine.
    monkeypatch.setattr(documents_route, "dense_index", None)

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


def test_upload_returns_while_background_indexing_is_queued(tmp_path: Path, monkeypatch):
    service = DocumentIngestionService(tmp_path / "data")
    queued: list[tuple[str, bool]] = []

    class FakeDense:
        model_ready = True

    class FakeQueue:
        def enqueue(self, document_id: str, force_rebuild: bool = False):
            queued.append((document_id, force_rebuild))
            service.mark_indexing_queued(document_id)
            return True

    monkeypatch.setattr(documents_route, "ingestion_service", service)
    monkeypatch.setattr(documents_route, "dense_index", FakeDense())
    monkeypatch.setattr(documents_route, "indexing_queue", FakeQueue())

    upload = client.post(
        "/api/upload",
        files={"files": ("policy.md", b"Remote work is allowed.", "text/markdown")},
        data={"category": "HR"},
    )

    assert upload.status_code == 200
    uploaded = upload.json()[0]
    assert uploaded["status"] == "processing"
    assert queued == [(uploaded["doc_id"], False)]


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
        def generate_answer(self, question, sources, chat_history=None, retrieval_profile="fast"):
            assert retrieval_profile == "fast"
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
    assert response.json()["citations"][0]["source_id"] == "S1"
    assert response.json()["citations"][0]["supported"] is True


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

        def search(self, question, category=None, final_k=5, candidate_k=30):
            del candidate_k
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
        def generate_answer(self, question, sources, chat_history=None, retrieval_profile="fast"):
            assert retrieval_profile == "quality"
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
    assert response.json()["citations"][0]["source_id"] == "S1"
