from datetime import datetime, timezone

import pytest
from models.contracts import (
    ChunkRecord,
    Citation,
    DocumentRecord,
    DocumentStatus,
    IngestionJob,
    RetrievalProfile,
    RetrievalResult,
)
from pydantic import ValidationError


def test_document_record_defaults_to_queued():
    now = datetime.now(timezone.utc)
    document = DocumentRecord(
        id="doc-1",
        filename="policy.md",
        sha256="a" * 64,
        size_bytes=42,
        created_at=now,
        updated_at=now,
    )

    assert document.status is DocumentStatus.QUEUED
    assert document.category == "General"


def test_retrieval_result_requires_a_positive_rank():
    with pytest.raises(ValidationError):
        RetrievalResult(
            chunk_id="chunk-1",
            document_id="doc-1",
            text="Evidence",
            rank=0,
            score=0.9,
            retrieval_profile=RetrievalProfile.FAST,
            filename="policy.md",
            location_type="paragraph",
            location_value="12",
        )


def test_citation_source_labels_are_machine_validated():
    citation = Citation(
        source_id="S1",
        chunk_id="chunk-1",
        document_id="doc-1",
        filename="policy.md",
        location_type="paragraph",
        location_value="12",
        excerpt="Evidence",
    )

    assert citation.source_id == "S1"


def test_ingestion_job_can_represent_a_failure():
    job = IngestionJob(
        id="job-1",
        document_id="doc-1",
        status=DocumentStatus.FAILED,
        error_detail="Unsupported file signature",
    )

    assert job.chunks_created == 0
    assert job.error_detail == "Unsupported file signature"


def test_chunk_record_rejects_empty_text():
    with pytest.raises(ValidationError):
        ChunkRecord(
            id="chunk-1",
            document_id="doc-1",
            block_id="block-1",
            text="",
            token_count=1,
            chunk_index=0,
            location_type="paragraph",
            location_value="1",
        )
