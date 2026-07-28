"""Validated local document ingestion and lifecycle management."""

from __future__ import annotations

import hashlib
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from models.contracts import (
    ChunkRecord,
    DocumentBlock,
    DocumentRecord,
    DocumentStatus,
    IngestionJob,
)
from pydantic import BaseModel
from services.embedder import DocumentProcessor
from services.metadata_store import MetadataStore
from services.settings import settings


class IngestionError(ValueError):
    """A safe, structured error that can be returned by the upload API."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class IngestionResult(BaseModel):
    document: DocumentRecord
    job: IngestionJob
    duplicate: bool = False
    replaced: bool = False


Indexer = Callable[[list[dict]], int | bool | None]

logger = logging.getLogger("docmind.ingestion")


class DocumentIngestionService:
    """Own validation, original-file storage, extraction, and document lifecycle."""

    OFFICE_EXTENSIONS = {".docx", ".pptx", ".xlsx"}

    def __init__(
        self,
        data_root: str | Path,
        metadata_store: Optional[MetadataStore] = None,
        processor: Optional[DocumentProcessor] = None,
        max_file_size: Optional[int] = None,
    ):
        self.data_root = Path(data_root)
        self.documents_root = self.data_root / "documents"
        self.documents_root.mkdir(parents=True, exist_ok=True)
        self.metadata_store = metadata_store or MetadataStore(self.data_root / "metadata.sqlite")
        self.processor = processor or DocumentProcessor()
        self.supported_extensions = set(settings.supported_extensions)
        self.max_file_size = max_file_size if max_file_size is not None else settings.max_file_size_mb * 1024 * 1024

    def validate_upload(
        self,
        filename: str,
        content: bytes,
        content_type: Optional[str] = None,
    ) -> str:
        del content_type  # MIME headers are client-controlled; signatures are authoritative.

        if not filename or "\x00" in filename or Path(filename).name != filename:
            raise IngestionError("invalid_filename", "Filename must be a simple local filename.")

        extension = Path(filename).suffix.lower()
        if extension not in self.supported_extensions:
            raise IngestionError(
                "unsupported_extension",
                f"Unsupported file type '{extension or '[none]'}'.",
            )
        if not content:
            raise IngestionError("empty_file", "The uploaded file is empty.")
        if len(content) > self.max_file_size:
            raise IngestionError(
                "file_too_large",
                f"The file exceeds the {self.max_file_size // (1024 * 1024)} MB limit.",
            )

        if extension == ".pdf" and not content.startswith(b"%PDF-"):
            raise IngestionError("invalid_signature", "The file is not a valid PDF signature.")
        if extension in self.OFFICE_EXTENSIONS and not content.startswith(b"PK"):
            raise IngestionError(
                "invalid_signature",
                "The file is not a valid Office Open XML container.",
            )
        if extension == ".xls" and not content.startswith(b"\xd0\xcf\x11\xe0"):
            raise IngestionError("invalid_signature", "The file is not a valid legacy XLS container.")
        return extension

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def ingest(
        self,
        filename: str,
        content: bytes,
        category: Optional[str] = None,
        replace: bool = False,
        indexer: Optional[Indexer] = None,
        content_type: Optional[str] = None,
    ) -> IngestionResult:
        started_at = time.perf_counter()
        stage = "validation"
        logger.info(
            "[UPLOAD] start file=%s size_bytes=%d category=%s embedding_enabled=%s",
            filename or "<missing>",
            len(content),
            category or settings.default_category,
            bool(indexer),
        )
        try:
            self.validate_upload(filename, content, content_type)
        except IngestionError as error:
            logger.warning(
                "[UPLOAD] rejected file=%s stage=%s code=%s elapsed_ms=%.1f",
                filename or "<missing>",
                stage,
                error.code,
                (time.perf_counter() - started_at) * 1000,
            )
            raise

        digest = self._hash(content)
        existing_hash = self.metadata_store.find_by_hash(digest)

        if existing_hash and not replace:
            logger.info(
                "[UPLOAD] duplicate file=%s document_id=%s elapsed_ms=%.1f",
                filename,
                existing_hash.id,
                (time.perf_counter() - started_at) * 1000,
            )
            job = IngestionJob(
                id=f"duplicate-{existing_hash.id}",
                document_id=existing_hash.id,
                status=existing_hash.status,
                chunks_created=existing_hash.chunk_count,
            )
            return IngestionResult(document=existing_hash, job=job, duplicate=True)

        existing_name = self.metadata_store.find_by_filename(filename)
        if existing_hash and (not existing_name or existing_hash.id != existing_name.id):
            raise IngestionError(
                "duplicate_content",
                f"The content is already stored as '{existing_hash.filename}'.",
            )
        if existing_name and existing_name.sha256 != digest and not replace:
            raise IngestionError(
                "duplicate_filename",
                f"A different document named '{filename}' already exists; set replace=true to replace it.",
            )

        document_id = existing_name.id if existing_name and replace else str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        now = self._now()
        original_path = self.documents_root / document_id / Path(filename).name
        document = DocumentRecord(
            id=document_id,
            filename=filename,
            sha256=digest,
            size_bytes=len(content),
            category=category.strip() if category and category.strip() else settings.default_category,
            status=DocumentStatus.QUEUED,
            original_path=str(original_path),
            created_at=existing_name.created_at if existing_name and replace else now,
            updated_at=now,
        )
        job = IngestionJob(id=job_id, document_id=document_id, status=DocumentStatus.QUEUED)
        self.metadata_store.save_document(document)
        self.metadata_store.save_job(job, now.isoformat(), now.isoformat())

        try:
            stage = "persist_original"
            document.status = DocumentStatus.PROCESSING
            job.status = DocumentStatus.PROCESSING
            document.updated_at = self._now()
            self.metadata_store.save_document(document)
            self.metadata_store.save_job(job, document.updated_at.isoformat(), document.updated_at.isoformat())

            original_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = original_path.with_suffix(f"{original_path.suffix}.tmp")
            temporary_path.write_bytes(content)
            os.replace(temporary_path, original_path)

            stage = "extraction"
            extraction_started_at = time.perf_counter()
            logger.info("[UPLOAD] extraction start file=%s", filename)
            raw_chunks = self.processor.extract_chunks(
                file_bytes=content,
                filename=filename,
                category=document.category,
                doc_id=document_id,
            )
            if not raw_chunks:
                raise IngestionError("extraction_empty", "No readable text was found in the document.")
            total_pages = max(int(chunk.get("total_pages", 1)) for chunk in raw_chunks)
            logger.info(
                "[UPLOAD] extraction complete file=%s chunks=%d pages=%d elapsed_ms=%.1f",
                filename,
                len(raw_chunks),
                total_pages,
                (time.perf_counter() - extraction_started_at) * 1000,
            )

            stage = "persist_content"
            blocks_by_id: dict[str, DocumentBlock] = {}
            chunks: list[ChunkRecord] = []
            for raw_chunk in raw_chunks:
                location_value = str(raw_chunk.get("page_number", 1))
                block_id = f"{document_id}:page:{location_value}"
                blocks_by_id.setdefault(
                    block_id,
                    DocumentBlock(
                        id=block_id,
                        document_id=document_id,
                        block_type="page",
                        text=raw_chunk["text"],
                        location_type="page",
                        location_value=location_value,
                    ),
                )
                chunks.append(
                    ChunkRecord(
                        id=raw_chunk["id"],
                        document_id=document_id,
                        block_id=block_id,
                        text=raw_chunk["text"],
                        token_count=max(1, len(raw_chunk["text"].split())),
                        chunk_index=raw_chunk["chunk_index"],
                        location_type="page",
                        location_value=location_value,
                    )
                )

            self.metadata_store.replace_content(document_id, blocks_by_id.values(), chunks)
            if indexer:
                stage = "embedding_indexing"
                indexing_started_at = time.perf_counter()
                logger.info(
                    "[UPLOAD] embedding/indexing start file=%s chunks=%d",
                    filename,
                    len(raw_chunks),
                )
                index_result = indexer(raw_chunks)
                logger.info(
                    "[UPLOAD] embedding/indexing complete file=%s result=%s elapsed_ms=%.1f",
                    filename,
                    index_result,
                    (time.perf_counter() - indexing_started_at) * 1000,
                )
                document.status = (
                    DocumentStatus.PARTIALLY_INDEXED
                    if index_result is False or index_result == 0
                    else DocumentStatus.INDEXED
                )
            else:
                document.status = DocumentStatus.PARTIALLY_INDEXED
            document.chunk_count = len(chunks)
            document.total_pages = max(int(chunk.location_value) for chunk in chunks)
            document.updated_at = self._now()
            job.status = document.status
            job.chunks_created = len(chunks)
            job.error_detail = None
            self.metadata_store.save_document(document)
            self.metadata_store.save_job(job, document.updated_at.isoformat(), document.updated_at.isoformat())
            logger.info(
                "[UPLOAD] complete file=%s document_id=%s status=%s chunks=%d elapsed_ms=%.1f",
                filename,
                document.id,
                document.status.value,
                document.chunk_count,
                (time.perf_counter() - started_at) * 1000,
            )
            return IngestionResult(
                document=document,
                job=job,
                replaced=bool(existing_name and replace),
            )
        except IngestionError as error:
            logger.error(
                "[UPLOAD] failed file=%s stage=%s code=%s elapsed_ms=%.1f",
                filename,
                stage,
                error.code,
                (time.perf_counter() - started_at) * 1000,
            )
            return self._mark_failed(document, job, error.message, error.code)
        except Exception as error:
            logger.exception(
                "[UPLOAD] failed file=%s stage=%s elapsed_ms=%.1f",
                filename,
                stage,
                (time.perf_counter() - started_at) * 1000,
            )
            return self._mark_failed(document, job, str(error), "ingestion_failed")

    def _mark_failed(
        self,
        document: DocumentRecord,
        job: IngestionJob,
        message: str,
        code: str,
    ) -> IngestionResult:
        document.status = DocumentStatus.FAILED
        document.error_detail = f"{code}: {message}"
        document.updated_at = self._now()
        job.status = DocumentStatus.FAILED
        job.error_detail = document.error_detail
        self.metadata_store.save_document(document)
        self.metadata_store.save_job(job, document.updated_at.isoformat(), document.updated_at.isoformat())
        return IngestionResult(document=document, job=job)

    def reindex(self, document_id: str, indexer: Optional[Indexer] = None) -> IngestionResult:
        document = self.metadata_store.get_document(document_id)
        if not document:
            raise IngestionError("not_found", f"Document '{document_id}' was not found.")
        original_path = Path(document.original_path)
        if not original_path.is_file():
            raise IngestionError("original_missing", "The original file is missing from local storage.")
        return self.ingest(
            filename=document.filename,
            content=original_path.read_bytes(),
            category=document.category,
            replace=True,
            indexer=indexer,
        )

    def delete(self, document_id: str) -> bool:
        document = self.metadata_store.get_document(document_id)
        if not document:
            return False
        deleted = self.metadata_store.delete_document(document_id)
        original_path = Path(document.original_path)
        if original_path.is_file():
            original_path.unlink()
        parent = original_path.parent
        if parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
        return deleted
