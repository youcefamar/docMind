import logging
from pathlib import Path

from models.contracts import DocumentStatus
from services.indexing_queue import BackgroundIndexQueue
from services.ingestion import DocumentIngestionService
from services.metadata_store import MetadataStore


def test_background_queue_indexes_extracted_document_without_reextraction(tmp_path: Path, caplog):
    caplog.set_level(logging.INFO, logger="docmind.index_queue")
    service = DocumentIngestionService(
        tmp_path / "data",
        metadata_store=MetadataStore(tmp_path / "data" / "metadata.sqlite"),
    )
    result = service.ingest("policy.md", b"Remote work is allowed.")
    indexed_ids: list[str] = []

    def indexer(document_id: str, force_rebuild: bool = False) -> int:
        indexed_ids.append(f"{document_id}:{force_rebuild}")
        return 1

    queue = BackgroundIndexQueue(service, indexer)

    assert queue.enqueue(result.document.id) is True
    assert queue.wait_for_idle(timeout=2) is True
    assert indexed_ids == [f"{result.document.id}:False"]
    assert service.metadata_store.get_document(result.document.id).status is DocumentStatus.INDEXED
    assert any("[INDEX_QUEUE] 📥 queued" in message for message in caplog.messages)
    assert any("[INDEX_QUEUE] 🎉 all queued indexing work is finished" in message for message in caplog.messages)


def test_catalog_rebuild_marks_only_affected_documents_indexed(tmp_path: Path):
    service = DocumentIngestionService(
        tmp_path / "data",
        metadata_store=MetadataStore(tmp_path / "data" / "metadata.sqlite"),
    )
    result = service.ingest("policy.md", b"Remote work is allowed.")
    indexed_ids: list[str] = []

    def indexer(document_id: str, force_rebuild: bool = False) -> int:
        indexed_ids.append(f"{document_id}:{force_rebuild}")
        return 1

    queue = BackgroundIndexQueue(service, indexer)

    assert queue.enqueue_rebuild([result.document.id]) is True
    assert queue.wait_for_idle(timeout=2) is True
    assert indexed_ids == ["<catalog-rebuild>:True"]
    assert service.metadata_store.get_document(result.document.id).status is DocumentStatus.INDEXED


def test_per_document_task_completes_without_nameerror(tmp_path: Path):
    """Regression: completed_documents was unbound on the per-document path,
    crashing the worker thread silently on the first non-catalog task."""
    service = DocumentIngestionService(
        tmp_path / "data",
        metadata_store=MetadataStore(tmp_path / "data" / "metadata.sqlite"),
    )
    result = service.ingest("policy.md", b"Remote work is allowed.")

    def indexer(document_id: str, force_rebuild: bool = False) -> int:
        return 1

    queue = BackgroundIndexQueue(service, indexer)

    assert queue.enqueue(result.document.id) is True
    assert queue.wait_for_idle(timeout=2) is True
    # Worker must still be alive — a second task must also complete
    result2 = service.ingest("notes.md", b"Annual leave is 25 days.")
    assert queue.enqueue(result2.document.id) is True
    assert queue.wait_for_idle(timeout=2) is True
    assert service.metadata_store.get_document(result2.document.id).status is DocumentStatus.INDEXED


def test_delete_enqueues_rebuild_with_correct_document_id(tmp_path: Path, monkeypatch):
    """Regression: enqueue_rebuild() was called with no args on delete,
    so complete_catalog_indexing received an empty set and updated nothing."""
    from routes import documents as documents_route

    service = DocumentIngestionService(tmp_path / "data")
    result = service.ingest("policy.md", b"Remote work is allowed.")
    doc_id = result.document.id

    rebuild_calls: list[list[str]] = []

    class FakeDense:
        model_ready = True

    class FakeQueue:
        def enqueue_rebuild(self, document_ids=()):
            rebuild_calls.append(list(document_ids))
            return True

    monkeypatch.setattr(documents_route, "ingestion_service", service)
    monkeypatch.setattr(documents_route, "dense_index", FakeDense())
    monkeypatch.setattr(documents_route, "indexing_queue", FakeQueue())

    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as client:
        response = client.delete(f"/api/doc/{doc_id}")

    assert response.status_code == 200
    assert rebuild_calls == [[doc_id]], (
        f"enqueue_rebuild must be called with [doc_id], got {rebuild_calls}"
    )

