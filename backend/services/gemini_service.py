"""
Gemini Service — Google Gemini API wrapper with streaming support.

Uses a shared httpx.AsyncClient for connection pooling and implements
Gemini safety settings for responsible AI usage. Falls back to curated
demo responses when no API key is configured.
"""

import json
import asyncio
from typing import AsyncGenerator, Optional

import httpx

from backend.config import (
    GEMINI_API_KEY,
    GEMINI_STREAM_URL,
    GEMINI_TIMEOUT_SECONDS,
    GEMINI_MAX_OUTPUT_TOKENS,
    GEMINI_TEMPERATURE,
    logger,
)


# ── Shared HTTP Client (initialized at startup) ──
_http_client: Optional[httpx.AsyncClient] = None


async def startup_client() -> None:
    """Initialize the shared httpx client with connection pooling."""
    global _http_client
    _http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(GEMINI_TIMEOUT_SECONDS, connect=10.0),
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        headers={"Content-Type": "application/json"},
    )
    logger.info("HTTP client initialized with connection pooling")


async def shutdown_client() -> None:
    """Close the shared httpx client and release connections."""
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None
        logger.info("HTTP client closed")


# ── Gemini Safety Settings ──
SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
]


# ── Fallback Responses (demo mode) ──
FALLBACK_RESPONSES = {
    "default": (
        "I'm ElectIQ, your election education assistant! I can help you "
        "understand the election process, voter registration, candidate "
        "nominations, and much more. Currently, I'm running in demo mode "
        "without an AI backend. To enable full AI responses, configure "
        "the GEMINI_API_KEY environment variable.\n\n"
        "📎 Source: Election Commission of India — eci.gov.in"
    ),
    "vote": (
        "To vote in Indian elections, you need to:\n\n"
        "• Be at least 18 years old\n"
        "• Be registered on the electoral roll\n"
        "• Carry a valid photo ID to the polling booth\n"
        "• Find your polling station at voters.eci.gov.in\n\n"
        "On voting day, go to your assigned booth, verify your identity, "
        "and cast your vote on the EVM (Electronic Voting Machine). "
        "A VVPAT slip will confirm your choice.\n\n"
        "📎 Source: Election Commission of India — eci.gov.in"
    ),
    "register": (
        "To register as a voter:\n\n"
        "• Visit voters.eci.gov.in\n"
        "• Fill out Form 6 (new registration)\n"
        "• Upload ID proof and address proof\n"
        "• Submit and track your application\n\n"
        "You can also visit your local Electoral Registration Officer. "
        "Processing takes 2-3 weeks.\n\n"
        "📎 Source: National Voters' Service Portal — voters.eci.gov.in"
    ),
    "candidate": (
        "To stand as a candidate in Indian elections:\n\n"
        "• Minimum age: 25 for Lok Sabha, 30 for Rajya Sabha\n"
        "• Must be a registered voter\n"
        "• File nomination with security deposit (₹25,000)\n"
        "• Disclose criminal record, assets & education\n"
        "• Follow the Model Code of Conduct\n\n"
        "📎 Source: Representation of the People Act, 1951"
    ),
    "evm": (
        "An EVM (Electronic Voting Machine) is a portable device used for "
        "casting votes electronically. Key facts:\n\n"
        "• Battery-operated, not connected to any network\n"
        "• Two parts: Ballot Unit (voter) + Control Unit (officer)\n"
        "• Can handle up to 64 candidates\n"
        "• VVPAT attached for paper verification\n"
        "• Used in India since 1982, universally since 2004\n\n"
        "📎 Source: Election Commission of India — eci.gov.in"
    ),
}

# Keyword-to-topic mapping for fallback response selection
_FALLBACK_KEYWORDS: list[tuple[list[str], str]] = [
    (["register", "registration", "form 6", "voter list"], "register"),
    (["vote", "voting", "poll", "booth", "ballot"], "vote"),
    (["candidate", "nomination", "contest", "stand for"], "candidate"),
    (["evm", "machine", "vvpat", "electronic"], "evm"),
]


def _get_fallback_response(message: str) -> str:
    """Select the most relevant fallback response based on keyword matching."""
    message_lower = message.lower()
    for keywords, topic in _FALLBACK_KEYWORDS:
        if any(kw in message_lower for kw in keywords):
            return FALLBACK_RESPONSES[topic]
    return FALLBACK_RESPONSES["default"]


async def stream_chat_response(
    system_prompt: str,
    message: str,
    history: list[dict],
) -> AsyncGenerator[str, None]:
    """
    Stream a response from the Gemini API via Server-Sent Events.

    If no API key is configured, falls back to curated demo responses
    with simulated streaming for a consistent user experience.

    Args:
        system_prompt: Role-aware system instruction for Gemini.
        message: The user's current question.
        history: Recent conversation turns for context.

    Yields:
        Text tokens as they arrive from Gemini, or word-by-word
        from fallback responses.
    """
    if not GEMINI_API_KEY:
        logger.info("Gemini API key not configured — using fallback response")
        fallback = _get_fallback_response(message)
        words = fallback.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.03)
        return

    # Build Gemini API request payload
    contents = []
    for entry in history:
        role = "user" if entry.get("role") == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": entry.get("content", "")}],
        })
    contents.append({
        "role": "user",
        "parts": [{"text": message}],
    })

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_prompt}],
        },
        "safetySettings": SAFETY_SETTINGS,
        "generationConfig": {
            "temperature": GEMINI_TEMPERATURE,
            "topP": 0.9,
            "topK": 40,
            "maxOutputTokens": GEMINI_MAX_OUTPUT_TOKENS,
        },
    }

    # Use API key as query parameter (required by Gemini REST API)
    url = f"{GEMINI_STREAM_URL}?alt=sse&key={GEMINI_API_KEY}"

    try:
        client = _http_client or httpx.AsyncClient(
            timeout=GEMINI_TIMEOUT_SECONDS
        )

        async with client.stream("POST", url, json=payload) as response:
            if response.status_code != 200:
                error_body = await response.aread()
                logger.error(
                    f"Gemini API error: status={response.status_code} "
                    f"body={error_body[:200]}"
                )
                yield (
                    "Sorry, I encountered an error connecting to the AI "
                    f"service. (Status: {response.status_code})"
                )
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
                            parts = (
                                candidates[0]
                                .get("content", {})
                                .get("parts", [])
                            )
                            for part in parts:
                                text = part.get("text", "")
                                if text:
                                    yield text
                    except json.JSONDecodeError:
                        continue

    except httpx.TimeoutException:
        logger.warning("Gemini API request timed out")
        yield "Sorry, the request timed out. Please try a shorter question."
    except Exception as exc:
        logger.error(f"Gemini API error: {exc}")
        yield f"Sorry, I encountered an error. Please try again."
