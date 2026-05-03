"""
Timeline Router — Serves election timeline milestone data from cache.

Provides the election process timeline with milestone details,
key facts, and FAQ data for the interactive timeline UI.
Includes HTTP caching headers for efficient client-side caching.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.config import DataCache, logger

__all__ = ["router"]

router = APIRouter()


@router.get(
    "/api/timeline",
    summary="Get election timeline",
    description="Returns all election process milestones with dates, "
    "descriptions, key facts, who's involved, and FAQ items.",
)
async def get_timeline() -> JSONResponse:
    """
    Return election timeline milestones from cached data.

    Returns:
        JSONResponse with timeline data and caching headers.
    """
    cache: DataCache = DataCache.get_instance()
    logger.info("Serving election timeline data")
    return JSONResponse(
        content=cache.timeline,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Vary": "Accept-Encoding",
        },
    )
