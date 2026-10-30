import logging

from fastapi import APIRouter
from models.contracts import CompareRequest, CompareResponse
from services.runtime import comparison_service

router = APIRouter(prefix="/api/compare", tags=["Compare"])
logger = logging.getLogger("docmind.compare")


@router.post("", response_model=CompareResponse)
@router.post("/", response_model=CompareResponse, include_in_schema=False)
async def compare_documents(request: CompareRequest) -> CompareResponse:
    """Compare two or more documents with structured markdown matrix generation."""
    logger.info(
        "[COMPARE] received request documents=%s focus=%s",
        request.document_ids,
        request.focus_aspect,
    )
    return comparison_service.compare_documents(
        document_ids=request.document_ids,
        focus_aspect=request.focus_aspect,
    )
