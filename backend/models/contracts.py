"""Stable contracts shared by ingestion, retrieval, and API layers.

These models intentionally do not depend on a particular vector database or
LLM runtime. That lets the product move from the current pgvector prototype to
the frozen local FAISS/BM25 pipeline without changing route contracts again.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from services.settings import settings


class DocumentStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    INDEXED = "indexed"
    PARTIALLY_INDEXED = "partially_indexed"
    FAILED = "failed"


class RetrievalProfile(str, Enum):
    FAST = "fast"
    QUALITY = "quality"


class DocumentRecord(BaseModel):
    id: str
    filename: str
    sha256: str = Field(min_length=64, max_length=64)
    size_bytes: int = Field(ge=0)
    category: str = Field(default_factory=lambda: settings.default_category)
    status: DocumentStatus = DocumentStatus.QUEUED
    created_at: datetime
    updated_at: datetime
    original_path: str = ""
    chunk_count: int = Field(default=0, ge=0)
    total_pages: int = Field(default=0, ge=0)
    error_detail: Optional[str] = None


class DocumentBlock(BaseModel):
    id: str
    document_id: str
    block_type: str = "paragraph"
    text: str = Field(min_length=1)
    location_type: str
    location_value: str


class ChunkRecord(BaseModel):
    id: str
    document_id: str
    block_id: str
    text: str = Field(min_length=1)
    token_count: int = Field(ge=1)
    chunk_index: int = Field(ge=0)
    location_type: str
    location_value: str


class RetrievalResult(BaseModel):
    chunk_id: str
    document_id: str
    text: str = Field(min_length=1)
    rank: int = Field(ge=1)
    score: float
    retrieval_profile: RetrievalProfile
    filename: str
    category: str = "General"
    location_type: str
    location_value: str


class Citation(BaseModel):
    source_id: str = Field(pattern=r"^S[1-9][0-9]*$")
    chunk_id: str
    document_id: str
    filename: str
    location_type: str
    location_value: str
    excerpt: str = Field(min_length=1)


class IngestionJob(BaseModel):
    id: str
    document_id: str
    status: DocumentStatus
    chunks_created: int = Field(default=0, ge=0)
    error_detail: Optional[str] = None
