from pathlib import Path

import pytest
from models.contracts import DocumentStatus
from services.ingestion import DocumentIngestionService, IngestionError
from services.metadata_store import MetadataStore


def make_service(tmp_path: Path) -> DocumentIngestionService:
    return DocumentIngestionService(
        data_root=tmp_path / "data",
        metadata_store=MetadataStore(tmp_path / "data" / "metadata.sqlite"),
    )


def test_ingest_stores_original_and_metadata(tmp_path: Path):
    service = make_service(tmp_path)

    result = service.ingest("policy.md", b"Remote work is allowed two days per week.")

    assert result.document.status is DocumentStatus.PARTIALLY_INDEXED
    assert result.document.chunk_count == 1
    assert Path(result.document.original_path).read_bytes().startswith(b"Remote work")
    assert len(service.metadata_store.get_chunks(result.document.id)) == 1


def test_same_content_is_idempotent(tmp_path: Path):
    service = make_service(tmp_path)
    content = b"The support team is available during business hours."

    first = service.ingest("support.txt", content)
    second = service.ingest("support.txt", content)

    assert second.duplicate is True
    assert second.document.id == first.document.id
    assert len(service.metadata_store.list_documents()) == 1


def test_different_content_requires_explicit_replace(tmp_path: Path):
    service = make_service(tmp_path)
    service.ingest("policy.md", b"Version one")

    with pytest.raises(IngestionError, match="already exists"):
        service.ingest("policy.md", b"Version two")


def test_replace_preserves_document_identity_and_updates_hash(tmp_path: Path):
    service = make_service(tmp_path)
    first = service.ingest("policy.md", b"Version one")

    replacement = service.ingest("policy.md", b"Version two", replace=True)

    assert replacement.replaced is True
    assert replacement.document.id == first.document.id
    assert replacement.document.sha256 != first.document.sha256
    assert Path(replacement.document.original_path).read_bytes() == b"Version two"


def test_invalid_pdf_signature_is_rejected(tmp_path: Path):
    service = make_service(tmp_path)

    with pytest.raises(IngestionError) as error:
        service.ingest("broken.pdf", b"not a pdf")

    assert error.value.code == "invalid_signature"


def test_delete_removes_metadata_and_original(tmp_path: Path):
    service = make_service(tmp_path)
    result = service.ingest("notes.txt", b"A local note.")
    original_path = Path(result.document.original_path)

    assert service.delete(result.document.id) is True
    assert not original_path.exists()
    assert service.metadata_store.get_document(result.document.id) is None
    assert service.delete(result.document.id) is False


def test_reindex_reads_the_stored_original(tmp_path: Path):
    service = make_service(tmp_path)
    first = service.ingest("notes.txt", b"A local note.")

    reindexed = service.reindex(first.document.id)

    assert reindexed.replaced is True
    assert reindexed.document.id == first.document.id
    assert reindexed.document.status is DocumentStatus.PARTIALLY_INDEXED
