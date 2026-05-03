"""
Gemini Service — Google Gemini API integration using the official SDK.

Uses the ``google-generativeai`` SDK for direct integration with
Google's Gemini models. Implements responsible AI safety settings,
streaming responses, and graceful fallback to curated demo responses
when no API key is configured.

Google Cloud Services:
    - Google Gemini 2.5 Flash (generative AI model)
    - Google AI Safety filters (harassment, hate, explicit, dangerous)
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Optional

from backend.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_MAX_OUTPUT_TOKENS,
    GEMINI_TEMPERATURE,
    logger,
)

__all__ = ["GeminiService"]

# ── Attempt to import Google Generative AI SDK ──
try:
    import google.generativeai as genai
    from google.generativeai.types import (
        HarmCategory,
        HarmBlockThreshold,
        GenerationConfig,
    )

    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False
    genai = None  # type: ignore[assignment]
    logger.warning(
        "google-generativeai SDK not installed; using HTTP fallback"
    )


class GeminiService:
    """
    Singleton service for Google Gemini API interactions.

    Encapsulates all Gemini API configuration, safety settings,
    and streaming logic. Replaces global state with a clean
    class-based pattern.

    Attributes:
        _initialized: Whether the service has been configured.
        _model_name: The Gemini model identifier to use.
    """

    _initialized: bool = False
    _model_name: str = GEMINI_MODEL

    @classmethod
    def initialize(cls) -> None:
        """
        Configure the Google Generative AI SDK with the API key.

        Called once during application startup. Safe to call multiple
        times (idempotent).
        """
        if cls._initialized:
            return

        if GEMINI_API_KEY and _SDK_AVAILABLE:
            genai.configure(api_key=GEMINI_API_KEY)
            logger.info(
                "Google Gemini SDK initialized with model: %s",
                cls._model_name,
            )
        elif not GEMINI_API_KEY:
            logger.info(
                "Gemini API key not configured — demo mode enabled"
            )
        cls._initialized = True

    @classmethod
    def is_available(cls) -> bool:
        """Check whether the Gemini API is configured and SDK is available."""
        return bool(GEMINI_API_KEY) and _SDK_AVAILABLE

    @classmethod
    def _create_model(
        cls, system_prompt: str
    ) -> Optional[object]:
        """
        Create a Gemini GenerativeModel instance with safety settings.

        Args:
            system_prompt: Role-aware system instruction for the model.

        Returns:
            Configured GenerativeModel instance, or None if unavailable.
        """
        if not cls.is_available():
            return None

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

        generation_config = GenerationConfig(
            temperature=GEMINI_TEMPERATURE,
            top_p=0.9,
            top_k=40,
            max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
        )

        return genai.GenerativeModel(
            model_name=cls._model_name,
            safety_settings=safety_settings,
            generation_config=generation_config,
            system_instruction=system_prompt,
        )


# ── Fallback Responses (Demo Mode) ──

FALLBACK_RESPONSES: dict[str, str] = {
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
    """
    Select the most relevant fallback response based on keyword matching.

    Args:
        message: The user's question to match against known topics.

    Returns:
        The most relevant curated response string.
    """
    message_lower = message.lower()
    for keywords, topic in _FALLBACK_KEYWORDS:
        if any(kw in message_lower for kw in keywords):
            return FALLBACK_RESPONSES[topic]
    return FALLBACK_RESPONSES["default"]


async def stream_chat_response(
    system_prompt: str,
    message: str,
    history: list[dict[str, str]],
) -> AsyncGenerator[str, None]:
    """
    Stream a response from the Google Gemini API.

    Uses the official ``google-generativeai`` SDK for direct integration
    with Google's AI services. If no API key is configured, falls back
    to curated demo responses with simulated streaming.

    Args:
        system_prompt: Role-aware system instruction for Gemini.
        message: The user's current question.
        history: Recent conversation turns for context.

    Yields:
        Text tokens as they arrive from Gemini, or word-by-word
        from fallback responses.
    """
    # ── Demo Mode (no API key) ──
    if not GeminiService.is_available():
        logger.info("Using fallback response (demo mode)")
        fallback = _get_fallback_response(message)
        words = fallback.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.03)
        return

    # ── Build conversation history for Gemini SDK ──
    contents: list[dict[str, object]] = []
    for entry in history:
        role = "user" if entry.get("role") == "user" else "model"
        contents.append({
            "role": role,
            "parts": [entry.get("content", "")],
        })
    contents.append({
        "role": "user",
        "parts": [message],
    })

    try:
        model = GeminiService._create_model(system_prompt)
        if model is None:
            yield _get_fallback_response(message)
            return

        # Use the SDK's async streaming API
        response = await model.generate_content_async(
            contents,
            stream=True,
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as exc:
        error_type = type(exc).__name__
        logger.error("Gemini API error (%s): %s", error_type, exc)

        # Fall back to curated responses on API error
        logger.info("Falling back to curated response after API error")
        fallback = _get_fallback_response(message)
        words = fallback.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.02)


# ── Legacy Compatibility ──


async def startup_client() -> None:
    """Initialize the Gemini service (legacy compatibility wrapper)."""
    GeminiService.initialize()


async def shutdown_client() -> None:
    """Clean up resources (no-op for SDK-based implementation)."""
    logger.info("Gemini service cleanup complete")
