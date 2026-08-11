import logging
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from models.contracts import DocumentStatus
from pydantic import BaseModel
from services.ingestion import IngestionError, IngestionResult
from services.runtime import dense_index, indexing_queue, ingestion_service
from services.settings import settings

router = APIRouter(prefix="/api", tags=["Documents"])
logger = logging.getLogger("docmind.documents")


class DocumentSummary(BaseModel):
    id: str
    filename: str
    category: str
    chunk_count: int
    total_pages: int
    created_at: str
    status: str
    error_detail: str | None = None


class UploadResponse(BaseModel):
    message: str
    doc_id: str
    filename: str
    category: str
    chunks_created: int
    total_pages: int
    status: str
    duplicate: bool = False
    replaced: bool = False
    error_detail: str | None = None


def _upload_response(result: IngestionResult) -> UploadResponse:
    return UploadResponse(
        message=(
            f"'{result.document.filename}' is already stored."
            if result.duplicate
            else f"Successfully stored and extracted '{result.document.filename}'."
        ),
        doc_id=result.document.id,
        filename=result.document.filename,
        category=result.document.category,
        chunks_created=result.document.chunk_count,
        total_pages=result.document.total_pages,
        status=result.document.status.value,
        duplicate=result.duplicate,
        replaced=result.replaced,
        error_detail=result.document.error_detail,
    )


@router.post("/upload", response_model=List[UploadResponse])
async def upload_documents(
    files: List[UploadFile] = File(...),
    category: str = Form(settings.default_category),
):
    """Validate, extract, and index uploaded documents locally when configured."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    responses = []
    for file in files:
        try:
            indexer_available = bool(dense_index and dense_index.model_ready)
            result = ingestion_service.ingest(
                filename=file.filename or "",
                content=await file.read(),
                category=category,
                content_type=file.content_type,
                indexer=None,
            )
            if indexer_available and not result.duplicate and result.document.status is not DocumentStatus.FAILED:
                indexing_queue.enqueue(result.document.id, force_rebuild=result.replaced)
                refreshed = ingestion_service.metadata_store.get_document(result.document.id)
                if refreshed:
                    result.document = refreshed
            responses.append(_upload_response(result))
        except IngestionError as error:
            raise HTTPException(
                status_code=400,
                detail={"code": error.code, "message": error.message},
            ) from error
        except Exception as error:
            logger.exception("[UPLOAD] request failed ❌ file=%s", file.filename or "<missing>")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document '{file.filename}': {error}",
            ) from error

    return responses


@router.post("/doc/{doc_id}/reindex", response_model=UploadResponse)
async def reindex_document(doc_id: str):
    try:
        indexer_available = bool(dense_index and dense_index.model_ready)
        result = ingestion_service.reindex(doc_id, indexer=None)
        if indexer_available and result.document.status is not DocumentStatus.FAILED:
            indexing_queue.enqueue(result.document.id, force_rebuild=True)
            refreshed = ingestion_service.metadata_store.get_document(result.document.id)
            if refreshed:
                result.document = refreshed
        return _upload_response(result)
    except IngestionError as error:
        status_code = 404 if error.code == "not_found" else 400
        raise HTTPException(
            status_code=status_code,
            detail={"code": error.code, "message": error.message},
        ) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to re-index document: {error}") from error


@router.get("/docs", response_model=List[DocumentSummary])
async def get_documents():
    try:
        documents = ingestion_service.metadata_store.list_documents()
        return [
            DocumentSummary(
                id=document.id,
                filename=document.filename,
                category=document.category,
                chunk_count=document.chunk_count,
                total_pages=document.total_pages,
                created_at=document.created_at.isoformat(),
                status=document.status.value,
                error_detail=document.error_detail,
            )
            for document in documents
        ]
    except Exception as error:
        logger.exception("[CATALOG] listing failed ❌")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {error}") from error


@router.delete("/doc/{doc_id}")
async def delete_document(doc_id: str):
    try:
        document = ingestion_service.metadata_store.get_document(doc_id)
        if not document or not ingestion_service.delete(doc_id):
            raise HTTPException(status_code=404, detail="Document not found.")
        if dense_index and dense_index.model_ready:
            indexing_queue.enqueue_rebuild([doc_id])

        return {
            "message": f"Successfully deleted document with ID '{doc_id}'",
            "chunks_removed": document.chunk_count,
        }
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("[DELETE] failed ❌ document_id=%s", doc_id)
        raise HTTPException(status_code=500, detail=f"Error deleting document: {error}") from error
