import os
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from services.ingestion import DocumentIngestionService, IngestionError

router = APIRouter(prefix="/api", tags=["Documents"])

DATA_ROOT = os.getenv(
    "DOCMIND_DATA_DIR",
    str(Path(__file__).resolve().parents[2] / "data"),
)
ingestion_service = DocumentIngestionService(DATA_ROOT)


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


@router.post("/upload", response_model=List[UploadResponse])
async def upload_documents(
    files: List[UploadFile] = File(...),
    category: str = Form("General"),
):
    """Validate, store, and extract uploaded documents locally.

    Vector indexing is intentionally a P2 concern. Until the FAISS/BM25
    indexer is connected, successful documents are returned as
    ``partially_indexed`` rather than being reported as fully indexed.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    responses = []
    for file in files:
        try:
            result = ingestion_service.ingest(
                filename=file.filename or "",
                content=await file.read(),
                category=category,
                content_type=file.content_type,
            )
            responses.append(
                UploadResponse(
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
            )
        except IngestionError as error:
            raise HTTPException(
                status_code=400,
                detail={"code": error.code, "message": error.message},
            ) from error
        except Exception as error:
            print(f"[Upload Error] File {file.filename}: {error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document '{file.filename}': {error}",
            ) from error

    return responses


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
        print(f"[Get Docs Error] {error}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {error}") from error


@router.delete("/doc/{doc_id}")
async def delete_document(doc_id: str):
    try:
        document = ingestion_service.metadata_store.get_document(doc_id)
        if not document or not ingestion_service.delete(doc_id):
            raise HTTPException(status_code=404, detail="Document not found.")

        return {
            "message": f"Successfully deleted document with ID '{doc_id}'",
            "chunks_removed": document.chunk_count,
        }
    except HTTPException:
        raise
    except Exception as error:
        print(f"[Delete Doc Error] {error}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {error}") from error
