"""
Chat Router — SSE streaming endpoint for AI-powered election chat.

Provides real-time streaming responses via Server-Sent Events with
input validation, rate-aware history trimming, and role-based
suggested questions powered by Google Gemini.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from backend.models import (
    ChatRequest,
    ChatSuggestionResponse,
    SuggestionQueryParams,
)
from backend.services.prompt_builder import (
    build_system_prompt,
    get_suggested_questions,
)
from backend.services.gemini_service import stream_chat_response
from backend.config import logger, MAX_CHAT_HISTORY_LENGTH

__all__ = ["router"]

router = APIRouter()


@router.post(
    "/api/chat",
    summary="Stream AI chat response",
    description="Send a message and receive a streamed AI response via "
    "Server-Sent Events. The response is contextualized based on the "
    "user's selected persona (voter, candidate, journalist, student). "
    "Powered by Google Gemini 2.5 Flash with safety filters.",
    response_description="SSE stream of JSON tokens",
    responses={
        422: {"description": "Validation error in request body"},
    },
)
async def chat(request: ChatRequest) -> StreamingResponse:
    """Stream an AI chat response via Server-Sent Events."""
    logger.info(
        "Chat request: role=%s message_length=%d history_length=%d",
        request.role,
        len(request.message),
        len(request.history),
    )

    system_prompt: str = build_system_prompt(request.role)

    # Trim history to prevent excessive token usage
    trimmed_history: list[dict[str, Any]] = request.history[
        -MAX_CHAT_HISTORY_LENGTH:
    ]

    async def event_stream():
        """Generate SSE events from Gemini streaming response."""
        async for token in stream_chat_response(
            system_prompt=system_prompt,
            message=request.message,
            history=trimmed_history,
        ):
            data = json.dumps({"token": token}, ensure_ascii=False)
            yield f"data: {data}\n\n"

        # Send completion signal
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/api/chat/suggestions",
    response_model=ChatSuggestionResponse,
    summary="Get suggested questions",
    description="Returns role-specific suggested starter questions "
    "to help users begin their election education journey.",
)
async def get_suggestions(
    role: str = Query(
        default="voter",
        description="User persona for suggested questions",
    ),
) -> ChatSuggestionResponse:
    """Get suggested starter questions for a given role."""
    params = SuggestionQueryParams(role=role)
    return ChatSuggestionResponse(
        suggestions=get_suggested_questions(params.role)
    )
