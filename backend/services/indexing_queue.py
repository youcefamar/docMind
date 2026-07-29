"""Single-worker background indexing for CPU-constrained local deployments."""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterable, Optional

from services.ingestion import DocumentIngestionService

logger = logging.getLogger("docmind.index_queue")


@dataclass(frozen=True)
class IndexTask:
    document_id: Optional[str]
    force_rebuild: bool = False


class BackgroundIndexQueue:
    """Serialize expensive local index work without blocking API requests."""

    def __init__(
        self,
        ingestion_service: DocumentIngestionService,
        indexer: Callable[..., int | bool | None],
    ):
        self.ingestion_service = ingestion_service
        self.indexer = indexer
        self._tasks: queue.Queue[IndexTask] = queue.Queue()
        self._pending: set[IndexTask] = set()
        self._active: Optional[IndexTask] = None
        self._last_error: Optional[str] = None
        self._last_completed_at: Optional[str] = None
        self._catalog_document_ids: set[str] = set()
        self._catalog_rebuild_followup_requested = False
        self._lock = threading.Lock()
        self._worker = threading.Thread(
            target=self._run,
            name="docmind-index-worker",
            daemon=True,
        )
        self._worker.start()

    def enqueue(self, document_id: str, force_rebuild: bool = False) -> bool:
        task = IndexTask(document_id=document_id, force_rebuild=force_rebuild)
        with self._lock:
            if any(item.document_id == document_id for item in self._pending):
                return False
            self._pending.add(task)
            self._last_error = None
        try:
            self.ingestion_service.mark_indexing_queued(document_id)
        except Exception:
            with self._lock:
                self._pending.discard(task)
            raise
        self._tasks.put(task)
        logger.info("[INDEX_QUEUE] queued document=%s force_rebuild=%s", document_id, force_rebuild)
        return True

    def enqueue_rebuild(self, document_ids: Iterable[str] = ()) -> bool:
        """Queue one atomic rebuild and finalize only the affected documents.

        Multiple changed/deleted files discovered in one folder scan share this
        task. A follow-up rebuild is safely queued if a second sync changes files
        while the current rebuild is already running.
        """
        requested_ids = {document_id for document_id in document_ids if document_id}
        task = IndexTask(document_id=None, force_rebuild=True)
        with self._lock:
            newly_tracked_ids = requested_ids - self._catalog_document_ids
            self._catalog_document_ids.update(requested_ids)
            already_scheduled = any(item.document_id is None for item in self._pending) or self._active == task
            if already_scheduled:
                if self._active == task:
                    self._catalog_rebuild_followup_requested = True
            else:
                self._pending.add(task)
                self._last_error = None
        for document_id in newly_tracked_ids:
            self.ingestion_service.mark_indexing_queued(document_id)
        if already_scheduled:
            return False
        self._tasks.put(task)
        logger.info(
            "[INDEX_QUEUE] queued full catalog rebuild affected_documents=%d",
            len(requested_ids),
        )
        return True

    def status(self) -> dict:
        with self._lock:
            active = self._active
            pending = list(self._pending)
            return {
                "status": "running" if active else "queued" if pending else "idle",
                "pending": len(pending),
                "active_document_id": active.document_id if active else None,
                "last_error": self._last_error,
                "last_completed_at": self._last_completed_at,
                "catalog_documents_pending": len(self._catalog_document_ids),
            }

    def wait_for_idle(self, timeout: float = 5.0) -> bool:
        """Wait for queued work to finish; primarily useful for integration tests."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.status()["status"] == "idle":
                return True
            time.sleep(0.01)
        return self.status()["status"] == "idle"

    def _run(self) -> None:
        while True:
            task = self._tasks.get()
            catalog_document_ids: set[str] = set()
            with self._lock:
                self._active = task
                if task.document_id is None:
                    catalog_document_ids = set(self._catalog_document_ids)
                    self._catalog_document_ids.clear()
            try:
                if task.document_id is None:
                    index_result = self.indexer("<catalog-rebuild>", force_rebuild=True)
                    self.ingestion_service.complete_catalog_indexing(
                        catalog_document_ids,
                        indexed=bool(index_result),
                    )
                else:
                    self.ingestion_service.index_existing(
                        task.document_id,
                        lambda document_id: self.indexer(
                            document_id,
                            force_rebuild=task.force_rebuild,
                        ),
                    )
                with self._lock:
                    self._last_completed_at = datetime.now(timezone.utc).isoformat()
                logger.info("[INDEX_QUEUE] completed document=%s", task.document_id or "<catalog>")
            except Exception as error:
                with self._lock:
                    self._last_error = str(error)
                logger.exception("[INDEX_QUEUE] failed document=%s", task.document_id or "<catalog>")
            finally:
                followup_task: Optional[IndexTask] = None
                with self._lock:
                    self._pending.discard(task)
                    self._active = None
                    if task.document_id is None and (
                        self._catalog_rebuild_followup_requested or self._catalog_document_ids
                    ):
                        followup_task = IndexTask(document_id=None, force_rebuild=True)
                        self._pending.add(followup_task)
                        self._catalog_rebuild_followup_requested = False
                if followup_task:
                    self._tasks.put(followup_task)
                    logger.info("[INDEX_QUEUE] queued follow-up full catalog rebuild")
                self._tasks.task_done()
