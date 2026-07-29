"""Synchronize a managed knowledge folder with the local document store."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from models.contracts import DocumentStatus
from services.ingestion import DocumentIngestionService, IngestionError
from services.metadata_store import MetadataStore
from services.settings import settings

logger = logging.getLogger("docmind.folder_sync")


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
        queue_document: Optional[Callable[[str, bool], bool]] = None,
        queue_rebuild: Optional[Callable[[list[str]], bool]] = None,
        manifest_path: str | Path | None = None,
    ):
        self.source_dir = Path(source_dir)
        self.source_dir.mkdir(parents=True, exist_ok=True)
        self.ingestion_service = ingestion_service
        self.metadata_store = metadata_store or ingestion_service.metadata_store
        self.queue_document = queue_document
        self.queue_rebuild = queue_rebuild
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
            "queued": 0,
            "rebuild_queued": False,
            "failures": [],
            "warnings": [],
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
                logger.info("[SYNC] ↪ already active status=%s", self._status["status"])
                return False
            self._status.update({"status": "queued", "error": None})
        logger.info("[SYNC] ⏳ queued folder=%s", self.source_dir.resolve())
        thread = threading.Thread(target=self.sync, name="docmind-folder-sync", daemon=True)
        thread.start()
        return True

    def sync(self) -> dict:
        """Synchronize the folder synchronously and return its final status."""
        started_at = time.perf_counter()
        with self._lock:
            if self._status["status"] == "syncing":
                logger.info("[SYNC] ↪ scan already running folder=%s", self.source_dir.resolve())
                return dict(self._status)
            self._status.update(
                {
                    "status": "syncing",
                    "discovered": 0,
                    "indexed": 0,
                    "unchanged": 0,
                    "removed": 0,
                    "failed": 0,
                    "queued": 0,
                    "rebuild_queued": False,
                    "failures": [],
                    "warnings": [],
                    "error": None,
                }
            )
        logger.info("[SYNC] 📂 started folder=%s", self.source_dir.resolve())

        try:
            result = self._sync_files()
            with self._lock:
                self._status.update(result)
                self._status.update(
                    {"status": "completed", "last_sync_at": datetime.now(timezone.utc).isoformat()}
                )
            logger.info(
                "[SYNC] ✅ scan complete discovered=%d extracted=%d unchanged=%d removed=%d "
                "failed=%d queued=%d rebuild_queued=%s elapsed_ms=%.1f",
                result["discovered"],
                result["indexed"],
                result["unchanged"],
                result["removed"],
                result["failed"],
                result["queued"],
                result["rebuild_queued"],
                (time.perf_counter() - started_at) * 1000,
            )
        except Exception as error:  # keep the API responsive after a bad source file
            logger.exception(
                "[SYNC] ❌ scan failed folder=%s elapsed_ms=%.1f",
                self.source_dir.resolve(),
                (time.perf_counter() - started_at) * 1000,
            )
            with self._lock:
                self._status.update(
                    {"status": "failed", "error": str(error), "last_sync_at": datetime.now(timezone.utc).isoformat()}
                )
        return self.status()

    def _sync_files(self) -> dict:
        manifest, manifest_warning = self._load_manifest()
        files = {
            path.relative_to(self.source_dir).as_posix(): path
            for path in self._iter_source_files()
        }
        logger.info("[SYNC] 🔎 discovered files=%d folder=%s", len(files), self.source_dir.resolve())
        counts = {
            "discovered": len(files),
            "indexed": 0,
            "unchanged": 0,
            "removed": 0,
            "failed": 0,
            "queued": 0,
            "rebuild_queued": False,
            "failures": [],
            "warnings": [manifest_warning] if manifest_warning else [],
        }
        if manifest_warning:
            logger.warning("[SYNC] ⚠️ %s", manifest_warning)
        next_manifest: dict[str, dict] = {}
        incremental_document_ids: set[str] = set()
        rebuild_document_ids: set[str] = set()
        requires_rebuild = False

        for position, (relative_path, path) in enumerate(sorted(files.items()), start=1):
            previous = manifest.get(relative_path, {})
            logger.info(
                "[SYNC] 📄 %d/%d checking file=%s",
                position,
                len(files),
                relative_path,
            )
            try:
                content = self._read_stable(path)
            except IngestionError as error:
                counts["failed"] += 1
                counts.setdefault("failures", []).append(
                    {"path": relative_path, "error": error.message}
                )
                if previous:
                    next_manifest[relative_path] = previous
                logger.error("[SYNC] ❌ read failed file=%s error=%s", relative_path, error.message)
                continue
            logger.info("[SYNC] 📥 read file=%s size_bytes=%d", relative_path, len(content))
            digest = hashlib.sha256(content).hexdigest()
            document = self.metadata_store.get_document(previous.get("doc_id", "")) if previous else None
            if (
                previous.get("sha256") == digest
                and document
                and self.metadata_store.get_chunks(document.id)
            ):
                if document.status == DocumentStatus.INDEXED or not self.queue_document:
                    counts["unchanged"] += 1
                    next_manifest[relative_path] = previous
                    logger.info(
                        "[SYNC] ↪ unchanged file=%s status=%s",
                        relative_path,
                        document.status.value,
                    )
                    continue
                incremental_document_ids.add(document.id)
                counts["unchanged"] += 1
                next_manifest[relative_path] = previous
                logger.info(
                    "[SYNC] ⏳ unchanged but indexing needed file=%s document_id=%s",
                    relative_path,
                    document.id,
                )
                continue

            managed = bool(previous.get("managed", True)) if previous else False
            display_name = (
                previous.get("filename")
                if previous and managed
                else self._display_filename(relative_path, manifest)
            )
            try:
                result = self.ingestion_service.ingest(
                    filename=display_name,
                    content=content,
                    category=self._category_for(relative_path),
                    replace=bool(document and managed),
                    indexer=None,
                )
                # A server interrupted during extraction can leave a valid hash
                # with no chunks. Repair it from the source bytes before any
                # background indexing task is scheduled.
                if result.duplicate and not self.metadata_store.get_chunks(result.document.id):
                    result = self.ingestion_service.ingest(
                        filename=result.document.filename,
                        content=content,
                        category=self._category_for(relative_path),
                        replace=True,
                        indexer=None,
                    )
                if result.document.status == DocumentStatus.FAILED:
                    raise IngestionError("ingestion_failed", result.document.error_detail or "Ingestion failed")
                next_manifest[relative_path] = {
                    "doc_id": result.document.id,
                    "filename": result.document.filename,
                    "sha256": digest,
                    # A duplicate may belong to a manual upload. Removing the source
                    # file must never delete a document that this sync did not create.
                    "managed": managed or not result.duplicate,
                }
                counts["indexed"] += 1
                if managed:
                    requires_rebuild = True
                    rebuild_document_ids.add(result.document.id)
                elif result.document.status != DocumentStatus.INDEXED:
                    incremental_document_ids.add(result.document.id)
                logger.info(
                    "[SYNC] ✅ extracted file=%s document_id=%s chunks=%d pages=%d status=%s",
                    relative_path,
                    result.document.id,
                    result.document.chunk_count,
                    result.document.total_pages,
                    result.document.status.value,
                )
            except Exception as error:
                counts["failed"] += 1
                counts.setdefault("failures", []).append(
                    {"path": relative_path, "error": str(error)}
                )
                if previous:
                    next_manifest[relative_path] = previous
                logger.exception("[SYNC] ❌ processing failed file=%s", relative_path)

        for relative_path, previous in manifest.items():
            if relative_path in files:
                continue
            document_id = previous.get("doc_id")
            if previous.get("managed", True) and document_id and self.ingestion_service.delete(document_id):
                counts["removed"] += 1
                requires_rebuild = True
                logger.info("[SYNC] 🗑️ removed missing source file=%s document_id=%s", relative_path, document_id)
            elif not previous.get("managed", True):
                counts["removed"] += 1
                logger.info("[SYNC] 🗑️ removed source mapping file=%s", relative_path)

        if requires_rebuild:
            # One atomic rebuild is enough for every changed, removed, and newly
            # extracted document in this scan. Never rebuild once per source file.
            rebuild_document_ids.update(incremental_document_ids)
            if self.queue_rebuild and self.queue_rebuild(sorted(rebuild_document_ids)):
                counts["queued"] = len(rebuild_document_ids)
                counts["rebuild_queued"] = True
                logger.info(
                    "[SYNC] ⏳ queued full rebuild affected_documents=%d",
                    len(rebuild_document_ids),
                )
        elif self.queue_document:
            for document_id in sorted(incremental_document_ids):
                if self.queue_document(document_id, False):
                    counts["queued"] += 1
            if counts["queued"]:
                logger.info("[SYNC] ⏳ queued incremental documents=%d", counts["queued"])

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

    def _source_identity(self) -> str:
        return str(self.source_dir.resolve())

    def _load_manifest(self) -> tuple[dict[str, dict], Optional[str]]:
        if not self.manifest_path.is_file():
            return {}, None
        try:
            payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                return {}, "Ignored an invalid knowledge-folder manifest."
            if payload.get("version") != 2:
                return {}, "Ignored a legacy manifest to protect documents from a stale source-folder mapping."
            if payload.get("source_dir") != self._source_identity():
                return {}, "Ignored a manifest created for a different knowledge folder."
            files = payload.get("files")
            if not isinstance(files, dict):
                return {}, "Ignored an invalid knowledge-folder manifest."
            return files, None
        except (OSError, json.JSONDecodeError):
            return {}, "Ignored an unreadable knowledge-folder manifest."

    def _save_manifest(self, manifest: dict[str, dict]) -> None:
        temporary = self.manifest_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(
                {
                    "version": 2,
                    "source_dir": self._source_identity(),
                    "files": manifest,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temporary.replace(self.manifest_path)
