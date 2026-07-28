from pathlib import Path

from models.contracts import DocumentStatus
from services.folder_sync import FolderSyncService
from services.ingestion import DocumentIngestionService
from services.metadata_store import MetadataStore


def make_sync(tmp_path: Path) -> tuple[FolderSyncService, Path]:
    data_root = tmp_path / "data"
    source_dir = tmp_path / "knowledge"
    service = DocumentIngestionService(
        data_root=data_root,
        metadata_store=MetadataStore(data_root / "metadata.sqlite"),
    )
    return FolderSyncService(source_dir, service), source_dir


def test_sync_indexes_new_file_and_is_idempotent(tmp_path: Path):
    sync, source_dir = make_sync(tmp_path)
    (source_dir / "policy.md").write_text("Remote work is allowed.", encoding="utf-8")

    first = sync.sync()
    second = sync.sync()

    assert first["discovered"] == 1
    assert first["indexed"] == 1
    assert second["unchanged"] == 1
    assert len(sync.metadata_store.list_documents()) == 1
    assert sync.metadata_store.list_documents()[0].status is DocumentStatus.PARTIALLY_INDEXED


def test_sync_replaces_changed_file_and_removes_deleted_file(tmp_path: Path):
    sync, source_dir = make_sync(tmp_path)
    source_file = source_dir / "policy.md"
    source_file.write_text("Version one", encoding="utf-8")
    sync.sync()
    document_id = sync.metadata_store.list_documents()[0].id

    source_file.write_text("Version two", encoding="utf-8")
    changed = sync.sync()
    assert changed["indexed"] == 1
    assert sync.metadata_store.get_document(document_id).sha256 != ""  # identity is preserved

    source_file.unlink()
    removed = sync.sync()
    assert removed["removed"] == 1
    assert sync.metadata_store.get_document(document_id) is None


def test_sync_ignores_unsupported_and_hidden_files(tmp_path: Path):
    sync, source_dir = make_sync(tmp_path)
    (source_dir / "notes.md").write_text("Included", encoding="utf-8")
    (source_dir / "image.png").write_bytes(b"ignored")
    (source_dir / ".hidden.md").write_text("ignored", encoding="utf-8")
    (source_dir / "partial.md.part").write_text("ignored", encoding="utf-8")

    result = sync.sync()

    assert result["discovered"] == 1
    assert len(sync.metadata_store.list_documents()) == 1


def test_sync_reports_failed_source_without_losing_previous_manifest(tmp_path: Path):
    sync, source_dir = make_sync(tmp_path)
    source_file = source_dir / "notes.txt"
    source_file.write_text("valid", encoding="utf-8")
    sync.sync()
    manifest = (tmp_path / "data" / "sync_manifest.json").read_text(encoding="utf-8")

    source_file.write_text("", encoding="utf-8")
    result = sync.sync()

    assert result["failed"] == 1
    assert (tmp_path / "data" / "sync_manifest.json").read_text(encoding="utf-8") == manifest
