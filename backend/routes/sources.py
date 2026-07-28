"""Managed knowledge-folder synchronization endpoints."""

from fastapi import APIRouter
from services.runtime import folder_sync_service

router = APIRouter(prefix="/api/sources", tags=["Knowledge Sources"])


@router.get("/status")
async def source_sync_status() -> dict:
    """Return the last and current source-folder synchronization state."""
    return folder_sync_service.status()


@router.post("/sync", status_code=202)
async def sync_sources() -> dict:
    """Queue a non-blocking scan of the configured knowledge folder."""
    queued = folder_sync_service.start_background()
    return {
        "message": "Knowledge-folder synchronization queued." if queued else "A synchronization is already running.",
        "queued": queued,
        "status": folder_sync_service.status(),
    }
