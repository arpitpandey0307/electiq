"""
Scenarios & Glossary Router — Serves interactive decision trees
and election term definitions from cached data.

Provides what-if scenario simulations and an expandable glossary
for the election education UI.
"""

from fastapi import APIRouter

from backend.config import DataCache, logger

router = APIRouter()


@router.get(
    "/api/scenarios",
    summary="Get what-if scenarios",
    description="Returns all interactive what-if scenario decision trees "
    "covering common election situations like missed registration, "
    "candidate withdrawal, and polling booth issues.",
)
async def get_scenarios():
    """Return all what-if scenarios from cached data."""
    cache = DataCache.get_instance()
    logger.info("Serving scenario data")
    return cache.scenarios


@router.get(
    "/api/glossary",
    summary="Get election glossary",
    description="Returns definitions for key electoral terms including "
    "short summaries and detailed explanations.",
)
async def get_glossary():
    """Return glossary of election terms from cached data."""
    cache = DataCache.get_instance()
    logger.info("Serving glossary data")
    return cache.glossary
