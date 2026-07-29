"""Safely retain only manifest-backed managed-knowledge documents.

This is an explicit one-time recovery tool for a catalog that predates the
managed knowledge-folder workflow. It requires a version-2 manifest and a
confirmation flag, creates a recoverable backup, removes untracked documents,
and marks retained documents for the next clean index build.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.ingestion import DocumentIngestionService
from services.metadata_store import MetadataStore


def _load_manifest(manifest_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read manifest '{manifest_path}': {error}") from error

    if payload.get("version") != 2 or not isinstance(payload.get("files"), dict):
        raise ValueError("A version-2 managed knowledge-folder manifest is required.")
    return payload


def _backup_artifacts(data_dir: Path, backup_root: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = backup_root / f"knowledge-catalog-migration-{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)

    for filename in ("metadata.sqlite", "sync_manifest.json"):
        source = data_dir / filename
        if source.is_file():
            shutil.copy2(source, backup_dir / filename)

    for dirname in ("documents", "indexes"):
        source = data_dir / dirname
        if source.is_dir():
            shutil.copytree(source, backup_dir / dirname)

    return backup_dir


def retain_knowledge_folder_catalog(
    data_dir: Path,
    manifest_path: Path | None = None,
    backup_root: Path | None = None,
    *,
    confirm: bool = False,
) -> dict[str, Any]:
    """Retain manifest documents only, with an explicit dry-run default."""
    data_dir = data_dir.resolve()
    manifest_path = (manifest_path or data_dir / "sync_manifest.json").resolve()
    backup_root = (backup_root or data_dir / "backups").resolve()
    manifest = _load_manifest(manifest_path)
    files = manifest["files"]
    retained_ids = {
        item.get("doc_id")
        for item in files.values()
        if isinstance(item, dict) and isinstance(item.get("doc_id"), str) and item["doc_id"]
    }
    if not retained_ids:
        raise ValueError("The manifest does not contain any document IDs to retain.")

    store = MetadataStore(data_dir / "metadata.sqlite")
    documents = store.list_documents()
    present_retained_ids = {document.id for document in documents if document.id in retained_ids}
    missing_retained_ids = sorted(retained_ids - present_retained_ids)
    if missing_retained_ids:
        raise ValueError(
            "The manifest references documents missing from SQLite: " + ", ".join(missing_retained_ids)
        )

    stale_documents = [document for document in documents if document.id not in retained_ids]
    summary: dict[str, Any] = {
        "data_dir": str(data_dir),
        "manifest_path": str(manifest_path),
        "retained_documents": len(present_retained_ids),
        "stale_documents": len(stale_documents),
        "stale_filenames": [document.filename for document in stale_documents],
        "confirmed": confirm,
        "backup_dir": None,
    }
    if not confirm:
        return summary

    backup_dir = _backup_artifacts(data_dir, backup_root)
    ingestion_service = DocumentIngestionService(data_dir, metadata_store=store)
    for document in stale_documents:
        if not ingestion_service.delete(document.id):
            raise RuntimeError(f"Failed to remove stale document '{document.filename}'.")

    # The user has explicitly adopted this folder as the source of truth. Future
    # file deletion from this folder can therefore remove its catalog document.
    for item in files.values():
        if isinstance(item, dict):
            item["managed"] = True
    temporary_manifest = manifest_path.with_suffix(".json.tmp")
    temporary_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary_manifest.replace(manifest_path)

    # Do not leave stale vectors searchable while waiting for the clean rebuild.
    indexes_dir = data_dir / "indexes"
    if indexes_dir.exists():
        shutil.rmtree(indexes_dir)
    indexes_dir.mkdir(parents=True, exist_ok=True)

    # The next source sync queues every retained document. The first job rebuilds
    # a clean FAISS/BM25 catalog, and the rest become safe no-op/append checks.
    ingestion_service.complete_catalog_indexing(retained_ids, indexed=False)
    summary["backup_dir"] = str(backup_dir)
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Retain only managed knowledge-folder documents.")
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[2] / "data")
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--backup-root", type=Path, default=None)
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required to create a backup and remove documents not in the manifest.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        summary = retain_knowledge_folder_catalog(
            args.data_dir,
            manifest_path=args.manifest,
            backup_root=args.backup_root,
            confirm=args.confirm,
        )
    except (OSError, RuntimeError, ValueError) as error:
        print(f"[KnowledgeCatalog] migration failed: {error}")
        return 1

    if not args.confirm:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print("Dry run only. Re-run with --confirm after stopping the backend.")
        return 0

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("Migration complete. Restart the backend and run one knowledge-folder sync to rebuild indexes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
