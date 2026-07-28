"""SQLite metadata persistence for the local ingestion pipeline."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Optional

from models.contracts import (
    ChunkRecord,
    DocumentBlock,
    DocumentRecord,
    DocumentStatus,
    IngestionJob,
)


class MetadataStore:
    """Small, file-backed metadata store for a single offline DocMind server."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    sha256 TEXT NOT NULL UNIQUE,
                    size_bytes INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL,
                    original_path TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL DEFAULT 0,
                    total_pages INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error_detail TEXT
                );

                CREATE INDEX IF NOT EXISTS documents_filename_idx
                    ON documents(filename);

                CREATE TABLE IF NOT EXISTS ingestion_jobs (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    chunks_created INTEGER NOT NULL DEFAULT 0,
                    error_detail TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS blocks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    block_type TEXT NOT NULL,
                    text TEXT NOT NULL,
                    location_type TEXT NOT NULL,
                    location_value TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    block_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    token_count INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    location_type TEXT NOT NULL,
                    location_value TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY(block_id) REFERENCES blocks(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS chunks_document_idx
                    ON chunks(document_id, chunk_index);
                """
            )

    @staticmethod
    def _document_values(document: DocumentRecord) -> tuple:
        return (
            document.id,
            document.filename,
            document.sha256,
            document.size_bytes,
            document.category,
            document.status.value,
            document.original_path,
            document.chunk_count,
            document.total_pages,
            document.created_at.isoformat(),
            document.updated_at.isoformat(),
            document.error_detail,
        )

    def save_document(self, document: DocumentRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    id, filename, sha256, size_bytes, category, status,
                    original_path, chunk_count, total_pages, created_at,
                    updated_at, error_detail
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    filename = excluded.filename,
                    sha256 = excluded.sha256,
                    size_bytes = excluded.size_bytes,
                    category = excluded.category,
                    status = excluded.status,
                    original_path = excluded.original_path,
                    chunk_count = excluded.chunk_count,
                    total_pages = excluded.total_pages,
                    updated_at = excluded.updated_at,
                    error_detail = excluded.error_detail
                """,
                self._document_values(document),
            )

    @staticmethod
    def _document_from_row(row: sqlite3.Row) -> DocumentRecord:
        return DocumentRecord(
            id=row["id"],
            filename=row["filename"],
            sha256=row["sha256"],
            size_bytes=row["size_bytes"],
            category=row["category"],
            status=DocumentStatus(row["status"]),
            original_path=row["original_path"],
            chunk_count=row["chunk_count"],
            total_pages=row["total_pages"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            error_detail=row["error_detail"],
        )

    def get_document(self, document_id: str) -> Optional[DocumentRecord]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE id = ?", (document_id,)
            ).fetchone()
        return self._document_from_row(row) if row else None

    def find_by_hash(self, sha256: str) -> Optional[DocumentRecord]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE sha256 = ?", (sha256,)
            ).fetchone()
        return self._document_from_row(row) if row else None

    def find_by_filename(self, filename: str) -> Optional[DocumentRecord]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE filename = ? ORDER BY created_at DESC LIMIT 1",
                (filename,),
            ).fetchone()
        return self._document_from_row(row) if row else None

    def list_documents(self) -> list[DocumentRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM documents ORDER BY created_at DESC"
            ).fetchall()
        return [self._document_from_row(row) for row in rows]

    def save_job(self, job: IngestionJob, created_at: str, updated_at: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO ingestion_jobs (
                    id, document_id, status, chunks_created, error_detail,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    chunks_created = excluded.chunks_created,
                    error_detail = excluded.error_detail,
                    updated_at = excluded.updated_at
                """,
                (
                    job.id,
                    job.document_id,
                    job.status.value,
                    job.chunks_created,
                    job.error_detail,
                    created_at,
                    updated_at,
                ),
            )

    def replace_content(
        self,
        document_id: str,
        blocks: Iterable[DocumentBlock],
        chunks: Iterable[ChunkRecord],
    ) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            connection.execute("DELETE FROM blocks WHERE document_id = ?", (document_id,))
            connection.executemany(
                """
                INSERT INTO blocks (
                    id, document_id, block_type, text, location_type, location_value
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        block.id,
                        block.document_id,
                        block.block_type,
                        block.text,
                        block.location_type,
                        block.location_value,
                    )
                    for block in blocks
                ],
            )
            connection.executemany(
                """
                INSERT INTO chunks (
                    id, document_id, block_id, text, token_count, chunk_index,
                    location_type, location_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.id,
                        chunk.document_id,
                        chunk.block_id,
                        chunk.text,
                        chunk.token_count,
                        chunk.chunk_index,
                        chunk.location_type,
                        chunk.location_value,
                    )
                    for chunk in chunks
                ],
            )

    def get_chunks(self, document_id: str) -> list[ChunkRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index",
                (document_id,),
            ).fetchall()
        return [
            ChunkRecord(
                id=row["id"],
                document_id=row["document_id"],
                block_id=row["block_id"],
                text=row["text"],
                token_count=row["token_count"],
                chunk_index=row["chunk_index"],
                location_type=row["location_type"],
                location_value=row["location_value"],
            )
            for row in rows
        ]

    def delete_document(self, document_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        return cursor.rowcount > 0
