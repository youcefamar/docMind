from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from services.ingestion import IngestionError
from services.runtime import dense_index, ingestion_service

router = APIRouter(prefix="/api", tags=["Documents"])


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
    """Validate, extract, and index uploaded documents locally when configured."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    responses = []
    for file in files:
        try:
            indexer = dense_index.index_document if dense_index and dense_index.model_ready else None
            result = ingestion_service.ingest(
                filename=file.filename or "",
                content=await file.read(),
                category=category,
                content_type=file.content_type,
                indexer=indexer,
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
        if dense_index and dense_index.model_ready:
            dense_index.rebuild_from_store()

        return {
            "message": f"Successfully deleted document with ID '{doc_id}'",
            "chunks_removed": document.chunk_count,
        }
    except HTTPException:
        raise
    except Exception as error:
        print(f"[Delete Doc Error] {error}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {error}") from error
