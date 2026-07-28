"""Synchronize a managed knowledge folder with the local document store."""

from __future__ import annotations

import hashlib
import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from models.contracts import DocumentStatus
from services.ingestion import DocumentIngestionService, IngestionError
from services.metadata_store import MetadataStore
from services.settings import settings


class FolderSyncService:
    """Track source files by relative path and reconcile additions, edits, and removals.

    The source folder is intentionally separate from ``data/documents``. The latter
    remains an ingestion-owned copy, while this service makes the source folder
    convenient for shared offline workstation use.
    """

    def __init__(
        self,
        source_dir: str | Path,
        ingestion_service: DocumentIngestionService,
        metadata_store: Optional[MetadataStore] = None,
        indexer: Optional[Callable[[str], int]] = None,
        manifest_path: str | Path | None = None,
    ):
        self.source_dir = Path(source_dir)
        self.source_dir.mkdir(parents=True, exist_ok=True)
        self.ingestion_service = ingestion_service
        self.metadata_store = metadata_store or ingestion_service.metadata_store
        self.indexer = indexer
        self.manifest_path = Path(manifest_path or ingestion_service.data_root / "sync_manifest.json")
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._status = {
            "status": "idle",
            "source_dir": str(self.source_dir.resolve()),
            "discovered": 0,
            "indexed": 0,
            "unchanged": 0,
            "removed": 0,
            "failed": 0,
            "failures": [],
            "last_sync_at": None,
            "error": None,
        }

    def status(self) -> dict:
        """Return a JSON-safe snapshot of the latest synchronization state."""
        with self._lock:
            return dict(self._status)

    def start_background(self) -> bool:
        """Queue one sync, returning false when another sync is already running."""
        with self._lock:
            if self._status["status"] in {"queued", "syncing"}:
                return False
            self._status.update({"status": "queued", "error": None})
        thread = threading.Thread(target=self.sync, name="docmind-folder-sync", daemon=True)
        thread.start()
        return True

    def sync(self) -> dict:
        """Synchronize the folder synchronously and return its final status."""
        with self._lock:
            if self._status["status"] == "syncing":
                return dict(self._status)
            self._status.update(
                {
                    "status": "syncing",
                    "discovered": 0,
                    "indexed": 0,
                    "unchanged": 0,
                    "removed": 0,
                    "failed": 0,
                    "failures": [],
                    "error": None,
                }
            )

        try:
            result = self._sync_files()
            with self._lock:
                self._status.update(result)
                self._status.update(
                    {"status": "completed", "last_sync_at": datetime.now(timezone.utc).isoformat()}
                )
        except Exception as error:  # keep the API responsive after a bad source file
            with self._lock:
                self._status.update(
                    {"status": "failed", "error": str(error), "last_sync_at": datetime.now(timezone.utc).isoformat()}
                )
        return self.status()

    def _sync_files(self) -> dict:
        manifest = self._load_manifest()
        files = {
            path.relative_to(self.source_dir).as_posix(): path
            for path in self._iter_source_files()
        }
        counts = {
            "discovered": len(files),
            "indexed": 0,
            "unchanged": 0,
            "removed": 0,
            "failed": 0,
            "failures": [],
        }
        next_manifest: dict[str, dict] = {}

        for relative_path, path in sorted(files.items()):
            previous = manifest.get(relative_path, {})
            try:
                content = self._read_stable(path)
            except IngestionError as error:
                counts["failed"] += 1
                counts.setdefault("failures", []).append(
                    {"path": relative_path, "error": error.message}
                )
                if previous:
                    next_manifest[relative_path] = previous
                print(f"[FolderSync] Failed to read {relative_path}: {error}")
                continue
            digest = hashlib.sha256(content).hexdigest()
            document = self.metadata_store.get_document(previous.get("doc_id", "")) if previous else None
            if previous.get("sha256") == digest and document:
                if document.status == DocumentStatus.INDEXED or not self.indexer:
                    counts["unchanged"] += 1
                    next_manifest[relative_path] = previous
                    continue
                try:
                    self.ingestion_service.reindex(document.id, indexer=self.indexer)
                    counts["indexed"] += 1
                    next_manifest[relative_path] = previous
                    continue
                except IngestionError:
                    pass

            display_name = previous.get("filename") or self._display_filename(relative_path, manifest)
            try:
                result = self.ingestion_service.ingest(
                    filename=display_name,
                    content=content,
                    category=self._category_for(relative_path),
                    replace=bool(document),
                    indexer=self.indexer,
                )
                if result.document.status == DocumentStatus.FAILED:
                    raise IngestionError("ingestion_failed", result.document.error_detail or "Ingestion failed")
                next_manifest[relative_path] = {
                    "doc_id": result.document.id,
                    "filename": result.document.filename,
                    "sha256": digest,
                }
                counts["indexed"] += 1
            except Exception as error:
                counts["failed"] += 1
                counts.setdefault("failures", []).append(
                    {"path": relative_path, "error": str(error)}
                )
                if previous:
                    next_manifest[relative_path] = previous
                print(f"[FolderSync] Failed to process {relative_path}: {error}")

        for relative_path, previous in manifest.items():
            if relative_path in files:
                continue
            document_id = previous.get("doc_id")
            if document_id and self.ingestion_service.delete(document_id):
                if self.indexer:
                    self.indexer(document_id)
                counts["removed"] += 1

        self._save_manifest(next_manifest)
        return counts

    def _iter_source_files(self) -> list[Path]:
        supported = {extension.lower() for extension in settings.supported_extensions}
        ignored_suffixes = {".part", ".tmp", ".crdownload"}
        return [
            path
            for path in self.source_dir.rglob("*")
            if path.is_file()
            and not any(part.startswith(".") for part in path.relative_to(self.source_dir).parts)
            and path.suffix.lower() in supported
            and path.suffix.lower() not in ignored_suffixes
        ]

    @staticmethod
    def _read_stable(path: Path) -> bytes:
        before = path.stat()
        content = path.read_bytes()
        after = path.stat()
        if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
            raise IngestionError("source_changing", "The source file changed while it was being read.")
        return content

    def _category_for(self, relative_path: str) -> str:
        parts = Path(relative_path).parts
        if len(parts) > 1:
            for category in settings.categories:
                if parts[0].casefold() == category.casefold():
                    return category
        return settings.default_category

    def _display_filename(self, relative_path: str, manifest: dict[str, dict]) -> str:
        filename = Path(relative_path).name
        used = {item.get("filename") for item in manifest.values()}
        if filename not in used and not self.metadata_store.find_by_filename(filename):
            return filename
        source_path = Path(relative_path)
        stem = re.sub(r"[^A-Za-z0-9._-]+", "_", source_path.with_suffix("").as_posix())
        suffix = source_path.suffix
        return f"{stem[:max(1, 240 - len(suffix))]}{suffix}"

    def _load_manifest(self) -> dict[str, dict]:
        if not self.manifest_path.is_file():
            return {}
        try:
            payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_manifest(self, manifest: dict[str, dict]) -> None:
        temporary = self.manifest_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.manifest_path)
