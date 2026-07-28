from pathlib import Path

from fastapi.testclient import TestClient
from main import app
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
