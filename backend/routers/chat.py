"""
Chat Router — SSE streaming endpoint for AI-powered election chat.

Provides real-time streaming responses via Server-Sent Events with
input validation, rate-aware history trimming, and role-based
suggested questions.
"""

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.models import ChatRequest, ChatSuggestionResponse
from backend.services.prompt_builder import build_system_prompt, get_suggested_questions
from backend.services.gemini_service import stream_chat_response
from backend.config import logger, MAX_CHAT_HISTORY_LENGTH

router = APIRouter()


@router.post(
    "/api/chat",
    summary="Stream AI chat response",
    description="Send a message and receive a streamed AI response via "
    "Server-Sent Events. The response is contextualized based on the "
    "user's selected persona (voter, candidate, journalist, student).",
    response_description="SSE stream of JSON tokens",
)
async def chat(request: ChatRequest):
    """Stream an AI chat response via Server-Sent Events."""
    logger.info(
        f"Chat request: role={request.role} "
        f"message_length={len(request.message)} "
        f"history_length={len(request.history)}"
    )

    system_prompt = build_system_prompt(request.role)

    # Trim history to prevent excessive token usage
    trimmed_history = request.history[-MAX_CHAT_HISTORY_LENGTH:]

    async def event_stream():
        async for token in stream_chat_response(
            system_prompt=system_prompt,
            message=request.message,
            history=trimmed_history,
        ):
            data = json.dumps({"token": token})
            yield f"data: {data}\n\n"

        # Send completion signal
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
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
async def get_suggestions(role: str = "voter") -> ChatSuggestionResponse:
    """Get suggested starter questions for a given role."""
    valid_roles = {"voter", "candidate", "journalist", "student"}
    safe_role = role.lower() if role.lower() in valid_roles else "voter"
    return ChatSuggestionResponse(
        suggestions=get_suggested_questions(safe_role)
    )
