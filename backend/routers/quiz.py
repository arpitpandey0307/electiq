"""
Quiz Router — Serves quiz questions by topic from cached data.

Uses the in-memory DataCache to serve quiz data without disk I/O
on each request. Provides both topic listing and per-topic question
retrieval with proper error responses.
"""

from fastapi import APIRouter, HTTPException

from backend.config import DataCache, logger
from backend.models import QuizTopicListResponse, QuizTopicSummary

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
async def get_quiz(topic: str):
    """Return quiz questions for a given topic from cached data."""
    cache = DataCache.get_instance()
    data = cache.quiz

    if topic not in data:
        available = ", ".join(data.keys()) if data else "none"
        logger.warning(f"Quiz topic not found: {topic}")
        raise HTTPException(
            status_code=404,
            detail=f"Topic '{topic}' not found. Available: {available}",
        )

    logger.info(f"Serving quiz topic: {topic}")
    return data[topic]


@router.get(
    "/api/quiz",
    response_model=QuizTopicListResponse,
    summary="List all quiz topics",
    description="Returns a summary of all available quiz topics including "
    "title, icon, and question count for the topic selector UI.",
)
async def list_quiz_topics() -> QuizTopicListResponse:
    """List all available quiz topics from cached data."""
    cache = DataCache.get_instance()
    data = cache.quiz

    topics = [
        QuizTopicSummary(
            id=key,
            title=value.get("title", key),
            icon=value.get("icon", "📝"),
            question_count=len(value.get("questions", [])),
        )
        for key, value in data.items()
    ]

    return QuizTopicListResponse(topics=topics)
