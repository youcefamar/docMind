from fastapi import APIRouter
from services.settings import settings

router = APIRouter(prefix="/api/config", tags=["Configuration"])


@router.get("/")
async def get_public_configuration() -> dict:
    """Expose safe UI/runtime options without exposing secrets or file paths."""

    return {
        "categories": list(settings.categories),
        "default_category": settings.default_category,
        "category_filter_options": ["All", *settings.categories],
        "supported_extensions": list(settings.supported_extensions),
        "max_file_size_mb": settings.max_file_size_mb,
        "retrieval_profiles": ["fast", "quality"],
        "retrieval_defaults": {
            "fast_top_k": settings.fast_top_k,
            "quality_final_k": settings.quality_final_k,
            "quality_candidate_k": settings.quality_candidate_k,
        },
        "suggested_prompts": list(settings.suggested_prompts),
    }
