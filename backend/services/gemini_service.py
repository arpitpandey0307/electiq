"""
Gemini Service — Google Gemini API wrapper with streaming support.
Falls back to a mock response when no API key is configured.
"""

import os
import json
import asyncio
from typing import AsyncGenerator

import httpx

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:streamGenerateContent"

# Fallback responses when no API key is set
FALLBACK_RESPONSES = {
    "default": "I'm ElectIQ, your election education assistant! I can help you understand the election process, voter registration, candidate nominations, and much more. Currently, I'm running in demo mode without an AI backend. To enable full AI responses, configure the GEMINI_API_KEY environment variable.\n\n📎 Source: Election Commission of India — eci.gov.in",
    "vote": "To vote in Indian elections, you need to:\n\n• Be at least 18 years old\n• Be registered on the electoral roll\n• Carry a valid photo ID to the polling booth\n• Find your polling station at voters.eci.gov.in\n\nOn voting day, go to your assigned booth, verify your identity, and cast your vote on the EVM (Electronic Voting Machine). A VVPAT slip will confirm your choice.\n\n📎 Source: Election Commission of India — eci.gov.in",
    "register": "To register as a voter:\n\n• Visit voters.eci.gov.in\n• Fill out Form 6 (new registration)\n• Upload ID proof and address proof\n• Submit and track your application\n\nYou can also visit your local Electoral Registration Officer. Processing takes 2-3 weeks.\n\n📎 Source: National Voters' Service Portal — voters.eci.gov.in",
    "candidate": "To stand as a candidate in Indian elections:\n\n• Minimum age: 25 for Lok Sabha, 30 for Rajya Sabha\n• Must be a registered voter\n• File nomination with security deposit (₹25,000)\n• Disclose criminal record, assets & education\n• Follow the Model Code of Conduct\n\n📎 Source: Representation of the People Act, 1951",
    "evm": "An EVM (Electronic Voting Machine) is a portable device used for casting votes electronically. Key facts:\n\n• Battery-operated, not connected to any network\n• Two parts: Ballot Unit (voter) + Control Unit (officer)\n• Can handle up to 64 candidates\n• VVPAT attached for paper verification\n• Used in India since 1982, universally since 2004\n\n📎 Source: Election Commission of India — eci.gov.in"
}


def _get_fallback_response(message: str) -> str:
    """Return a relevant fallback response based on keywords in the message."""
    message_lower = message.lower()
    
    if any(w in message_lower for w in ["register", "registration", "form 6", "voter list"]):
        return FALLBACK_RESPONSES["register"]
    elif any(w in message_lower for w in ["vote", "voting", "poll", "booth", "ballot"]):
        return FALLBACK_RESPONSES["vote"]
    elif any(w in message_lower for w in ["candidate", "nomination", "contest", "stand for"]):
        return FALLBACK_RESPONSES["candidate"]
    elif any(w in message_lower for w in ["evm", "machine", "vvpat", "electronic"]):
        return FALLBACK_RESPONSES["evm"]
    else:
        return FALLBACK_RESPONSES["default"]


async def stream_chat_response(
    system_prompt: str,
    message: str,
    history: list[dict]
) -> AsyncGenerator[str, None]:
    """
    Stream a response from Gemini API, or fallback if no key configured.
    Yields text tokens one at a time for SSE streaming.
    """
    
    if not GEMINI_API_KEY:
        # Fallback mode — simulate streaming with mock response
        fallback = _get_fallback_response(message)
        words = fallback.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.03)
        return
    
    # Build Gemini API request
    contents = []
    
    # Add conversation history
    for entry in history:
        role = "user" if entry.get("role") == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": entry.get("content", "")}]
        })
    
    # Add current message
    contents.append({
        "role": "user",
        "parts": [{"text": message}]
    })
    
    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.9,
            "topK": 40,
            "maxOutputTokens": 1024
        }
    }
    
    url = f"{GEMINI_URL}?alt=sse&key={GEMINI_API_KEY}"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    yield f"Sorry, I encountered an error connecting to the AI service. Please try again. (Status: {response.status_code})"
                    return
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for part in parts:
                                    text = part.get("text", "")
                                    if text:
                                        yield text
                        except json.JSONDecodeError:
                            continue
    except httpx.TimeoutException:
        yield "Sorry, the request timed out. Please try again with a shorter question."
    except Exception as e:
        yield f"Sorry, I encountered an error: {str(e)}. Please try again."
