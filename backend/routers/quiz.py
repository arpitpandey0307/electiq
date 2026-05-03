"""
Quiz Router — Serves quiz questions by topic from cached data.

Uses the in-memory DataCache to serve quiz data without disk I/O
on each request. Provides both topic listing and per-topic question
retrieval with proper error responses and HTTP caching.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.config import DataCache, logger
from backend.models import QuizTopicListResponse, QuizTopicSummary

__all__ = ["router"]

router = APIRouter()


@router.get(
    "/api/quiz/{topic}",
    summary="Get quiz questions for a topic",
    description="Returns all questions for a specific quiz topic including "
    "options, correct answers, and explanations.",
    responses={
        404: {"description": "Topic not found"},
    },
)
async def get_quiz(topic: str) -> JSONResponse:
    """
    Return quiz questions for a given topic from cached data.

    Args:
        topic: Quiz topic identifier (e.g., 'voter-registration').

    Returns:
        JSONResponse with quiz data and cache headers.

    Raises:
        HTTPException: 404 if the topic is not found.
    """
    cache: DataCache = DataCache.get_instance()
    data: dict[str, Any] = cache.quiz

    if topic not in data:
        available = ", ".join(data.keys()) if data else "none"
        logger.warning("Quiz topic not found: %s", topic)
        raise HTTPException(
            status_code=404,
            detail=f"Topic '{topic}' not found. Available: {available}",
        )

    logger.info("Serving quiz topic: %s", topic)
    return JSONResponse(
        content=data[topic],
        headers={
            "Cache-Control": "public, max-age=3600",
            "Vary": "Accept-Encoding",
        },
    )


@router.get(
    "/api/quiz",
    response_model=QuizTopicListResponse,
    summary="List all quiz topics",
    description="Returns a summary of all available quiz topics including "
    "title, icon, and question count for the topic selector UI.",
)
async def list_quiz_topics() -> QuizTopicListResponse:
    """
    List all available quiz topics from pre-computed cache.

    Returns:
        QuizTopicListResponse with topic summaries.
    """
    cache: DataCache = DataCache.get_instance()
    topics: list[QuizTopicSummary] = [
        QuizTopicSummary(**summary)
        for summary in cache.quiz_topic_summaries
    ]
    return QuizTopicListResponse(topics=topics)
