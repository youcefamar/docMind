import json
from pathlib import Path

from scripts.retain_knowledge_folder import retain_knowledge_folder_catalog
from services.ingestion import DocumentIngestionService
from services.metadata_store import MetadataStore


def test_retain_knowledge_folder_catalog_dry_run_keeps_everything(tmp_path: Path):
    data_dir = tmp_path / "data"
    service = DocumentIngestionService(data_dir, metadata_store=MetadataStore(data_dir / "metadata.sqlite"))
    retained = service.ingest("policy.md", b"Remote work is allowed.").document
    stale = service.ingest("old.md", b"Old document.").document
    manifest_path = data_dir / "sync_manifest.json"
    manifest_path.write_text(
        json.dumps({"version": 2, "source_dir": "C:/knowledge", "files": {"policy.md": {"doc_id": retained.id}}}),
        encoding="utf-8",
    )

    result = retain_knowledge_folder_catalog(data_dir, confirm=False)

    assert result["retained_documents"] == 1
    assert result["stale_documents"] == 1
    assert service.metadata_store.get_document(stale.id) is not None


def test_retain_knowledge_folder_catalog_backs_up_and_removes_stale_documents(tmp_path: Path):
    data_dir = tmp_path / "data"
    service = DocumentIngestionService(data_dir, metadata_store=MetadataStore(data_dir / "metadata.sqlite"))
    retained = service.ingest("policy.md", b"Remote work is allowed.").document
    stale = service.ingest("old.md", b"Old document.").document
    manifest_path = data_dir / "sync_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "version": 2,
                "source_dir": "C:/knowledge",
                "files": {"policy.md": {"doc_id": retained.id, "managed": False}},
            }
        ),
        encoding="utf-8",
    )

    result = retain_knowledge_folder_catalog(data_dir, backup_root=tmp_path / "backups", confirm=True)
    updated_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert Path(result["backup_dir"]).is_dir()
    assert (Path(result["backup_dir"]) / "metadata.sqlite").is_file()
    assert service.metadata_store.get_document(stale.id) is None
    assert service.metadata_store.get_document(retained.id).status.value == "partially_indexed"
    assert updated_manifest["files"]["policy.md"]["managed"] is True
    assert (data_dir / "indexes").is_dir()
