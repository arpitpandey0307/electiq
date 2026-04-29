"""
Chat Router — SSE streaming endpoint for AI chat.
"""

import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.services.prompt_builder import build_system_prompt, get_suggested_questions
from backend.services.gemini_service import stream_chat_response

router = APIRouter()


class ChatRequest(BaseModel):
    role: str = "voter"
    message: str
    history: list[dict] = []


@router.post("/api/chat")
async def chat(request: ChatRequest):
    """Stream AI chat response via Server-Sent Events."""
    system_prompt = build_system_prompt(request.role)
    
    async def event_stream():
        async for token in stream_chat_response(
            system_prompt=system_prompt,
            message=request.message,
            history=request.history
        ):
            data = json.dumps({"token": token})
            yield f"data: {data}\n\n"
        
        # Send done signal
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/api/chat/suggestions")
async def get_suggestions(role: str = "voter"):
    """Get suggested questions for a role."""
    return {"suggestions": get_suggested_questions(role)}
