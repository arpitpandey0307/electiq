"""
Timeline Router — Serves election timeline milestone data from cache.

Provides the election process timeline with milestone details,
key facts, and FAQ data for the interactive timeline UI.
"""

from fastapi import APIRouter

from backend.config import DataCache, logger

router = APIRouter()


@router.get(
    "/api/timeline",
    summary="Get election timeline",
    description="Returns all election process milestones with dates, "
    "descriptions, key facts, who's involved, and FAQ items.",
)
async def get_timeline():
    """Return election timeline milestones from cached data."""
    cache = DataCache.get_instance()
    logger.info("Serving election timeline data")
    return cache.timeline
