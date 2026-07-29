import json
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
    assert result["failures"][0]["path"] == "notes.txt"
    assert (tmp_path / "data" / "sync_manifest.json").read_text(encoding="utf-8") == manifest


def test_sync_queues_new_file_for_incremental_indexing(tmp_path: Path):
    data_root = tmp_path / "data"
    source_dir = tmp_path / "knowledge"
    service = DocumentIngestionService(
        data_root=data_root,
        metadata_store=MetadataStore(data_root / "metadata.sqlite"),
    )
    queued: list[tuple[str, bool]] = []
    sync = FolderSyncService(
        source_dir,
        service,
        queue_document=lambda document_id, force_rebuild: queued.append((document_id, force_rebuild)) or True,
    )
    (source_dir / "policy.md").parent.mkdir(parents=True, exist_ok=True)
    (source_dir / "policy.md").write_text("Remote work is allowed.", encoding="utf-8")

    result = sync.sync()

    document = service.metadata_store.list_documents()[0]
    assert result["queued"] == 1
    assert result["rebuild_queued"] is False
    assert queued == [(document.id, False)]
    assert document.status is DocumentStatus.PARTIALLY_INDEXED


def test_changed_source_queues_one_full_rebuild_for_the_scan(tmp_path: Path):
    sync, source_dir = make_sync(tmp_path)
    source_file = source_dir / "policy.md"
    source_file.write_text("Version one", encoding="utf-8")
    sync.sync()
    document_id = sync.metadata_store.list_documents()[0].id

    rebuilds: list[list[str]] = []
    queued_sync = FolderSyncService(
        source_dir,
        sync.ingestion_service,
        metadata_store=sync.metadata_store,
        queue_document=lambda *_args: True,
        queue_rebuild=lambda document_ids: rebuilds.append(document_ids) or True,
    )
    source_file.write_text("Version two", encoding="utf-8")

    result = queued_sync.sync()

    assert result["rebuild_queued"] is True
    assert result["queued"] == 1
    assert rebuilds == [[document_id]]


def test_legacy_manifest_cannot_delete_documents_from_another_source_root(tmp_path: Path):
    data_root = tmp_path / "data"
    source_dir = tmp_path / "knowledge"
    service = DocumentIngestionService(
        data_root=data_root,
        metadata_store=MetadataStore(data_root / "metadata.sqlite"),
    )
    outside = service.ingest("outside.md", b"Keep this document.").document
    (data_root / "sync_manifest.json").write_text(
        json.dumps(
            {
                "outside.md": {
                    "doc_id": outside.id,
                    "filename": outside.filename,
                    "sha256": outside.sha256,
                }
            }
        ),
        encoding="utf-8",
    )
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "policy.md").write_text("In the managed folder.", encoding="utf-8")

    result = FolderSyncService(source_dir, service).sync()

    assert service.metadata_store.get_document(outside.id) is not None
    assert result["removed"] == 0
    assert result["warnings"]


def test_sync_repairs_interrupted_document_before_queueing_it(tmp_path: Path):
    sync, source_dir = make_sync(tmp_path)
    source_file = source_dir / "policy.md"
    source_file.write_text("Remote work is allowed.", encoding="utf-8")
    sync.sync()
    document = sync.metadata_store.list_documents()[0]
    sync.metadata_store.replace_content(document.id, [], [])

    result = sync.sync()

    assert result["indexed"] == 1
    assert sync.metadata_store.get_chunks(document.id)
