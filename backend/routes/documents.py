from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from services.embedder import DocumentProcessor, EmbeddingService
from services.retriever import VectorStoreService

router = APIRouter(prefix="/api", tags=["Documents"])

doc_processor = DocumentProcessor()
embedder_service = EmbeddingService()
retriever_service = VectorStoreService()

ALLOWED_EXTENSIONS = ('.pdf', '.docx', '.xlsx', '.xls', '.pptx', '.txt', '.md')

class DocumentSummary(BaseModel):
    id: str
    filename: str
    category: str
    chunk_count: int
    total_pages: int
    created_at: str

class UploadResponse(BaseModel):
    message: str
    doc_id: str
    filename: str
    category: str
    chunks_created: int
    total_pages: int

@router.post("/upload", response_model=List[UploadResponse])
async def upload_documents(
    files: List[UploadFile] = File(...),
    category: str = Form("General")
):
    """
    Accepts PDF, DOCX, XLSX, PPTX, or TXT documents, extracts text,
    chunks, embeds, and stores in PostgreSQL pgvector.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    responses = []

    for file in files:
        ext = file.filename.lower()
        if not ext.endswith(ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type for '{file.filename}'. Supported formats: PDF, DOCX, XLSX, PPTX, TXT, MD."
            )

        try:
            content = await file.read()
            chunks = doc_processor.extract_chunks(
                file_bytes=content,
                filename=file.filename,
                category=category
            )

            if not chunks:
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not extract readable text from document '{file.filename}'."
                )

            texts = [c["text"] for c in chunks]
            embeddings = embedder_service.generate_embeddings(texts)
            retriever_service.add_document_chunks(chunks, embeddings)

            doc_id = chunks[0]["doc_id"]
            total_pages = chunks[0]["total_pages"]

            responses.append(UploadResponse(
                message=f"Successfully processed and indexed '{file.filename}'",
                doc_id=doc_id,
                filename=file.filename,
                category=category,
                chunks_created=len(chunks),
                total_pages=total_pages
            ))

        except HTTPException as he:
            raise he
        except Exception as e:
            print(f"[Upload Error] File {file.filename}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document '{file.filename}': {str(e)}"
            )

    return responses


@router.get("/docs", response_model=List[DocumentSummary])
async def get_documents():
    try:
        documents = retriever_service.list_all_documents()
        return [DocumentSummary(**doc) for doc in documents]
    except Exception as e:
        print(f"[Get Docs Error] {e}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@router.delete("/doc/{doc_id}")
async def delete_document(doc_id: str):
    try:
        deleted_count = retriever_service.delete_document_by_id(doc_id)
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found.")

        return {
            "message": f"Successfully deleted document with ID '{doc_id}'",
            "chunks_removed": deleted_count
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[Delete Doc Error] {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")
