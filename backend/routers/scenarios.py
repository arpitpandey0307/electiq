"""
Scenarios & Glossary Router — Serves interactive decision trees
and election term definitions from cached data.

Provides what-if scenario simulations and an expandable glossary
for the election education UI with proper HTTP caching.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.config import DataCache, logger

__all__ = ["router"]

router = APIRouter()


@router.get(
    "/api/scenarios",
    summary="Get what-if scenarios",
    description="Returns all interactive what-if scenario decision trees "
    "covering common election situations like missed registration, "
    "candidate withdrawal, and polling booth issues.",
)
async def get_scenarios() -> JSONResponse:
    """
    Return all what-if scenarios from cached data.

    Returns:
        JSONResponse with scenario data and caching headers.
    """
    cache: DataCache = DataCache.get_instance()
    logger.info("Serving scenario data")
    return JSONResponse(
        content=cache.scenarios,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Vary": "Accept-Encoding",
        },
    )


@router.get(
    "/api/glossary",
    summary="Get election glossary",
    description="Returns definitions for key electoral terms including "
    "short summaries and detailed explanations.",
)
async def get_glossary() -> JSONResponse:
    """
    Return glossary of election terms from cached data.

    Returns:
        JSONResponse with glossary data and caching headers.
    """
    cache: DataCache = DataCache.get_instance()
    logger.info("Serving glossary data")
    return JSONResponse(
        content=cache.glossary,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Vary": "Accept-Encoding",
        },
    )
