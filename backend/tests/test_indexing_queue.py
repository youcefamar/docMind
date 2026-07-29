from pathlib import Path

from models.contracts import DocumentStatus
from services.indexing_queue import BackgroundIndexQueue
from services.ingestion import DocumentIngestionService
from services.metadata_store import MetadataStore


def test_background_queue_indexes_extracted_document_without_reextraction(tmp_path: Path):
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
