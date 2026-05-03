"""
Gemini Service Tests for ElectIQ.

Tests the Google Gemini AI service including fallback responses,
keyword matching, streaming, and error handling.
"""

import pytest

from backend.services.gemini_service import (
    GeminiService,
    FALLBACK_RESPONSES,
    _get_fallback_response,
    stream_chat_response,
)


class TestGeminiServiceInit:
    """Test service initialization and configuration."""

    def test_service_is_class(self):
        """GeminiService should be a proper class."""
        assert hasattr(GeminiService, "initialize")
        assert hasattr(GeminiService, "is_available")

    def test_initialize_idempotent(self):
        """Multiple initialize calls should be safe."""
        GeminiService._initialized = False
        GeminiService.initialize()
        GeminiService.initialize()  # Should not raise

    def test_is_available_check(self):
        """is_available should reflect API key configuration."""
        result = GeminiService.is_available()
        assert isinstance(result, bool)


class TestFallbackResponses:
    """Test curated fallback response system."""

    def test_fallback_responses_not_empty(self):
        """All fallback responses should have content."""
        for key, value in FALLBACK_RESPONSES.items():
            assert len(value) > 50, f"Fallback '{key}' is too short"

    def test_fallback_has_source_citation(self):
        """All fallback responses should cite a source."""
        for key, value in FALLBACK_RESPONSES.items():
            assert "📎" in value or "Source:" in value, \
                f"Fallback '{key}' missing source citation"

    def test_keyword_matching_vote(self):
        result = _get_fallback_response("How do I vote?")
        assert "vote" in result.lower() or "poll" in result.lower()

    def test_keyword_matching_register(self):
        result = _get_fallback_response("How to register to vote?")
        assert "register" in result.lower() or "Form 6" in result

    def test_keyword_matching_candidate(self):
        result = _get_fallback_response("How to stand as a candidate?")
        assert "candidate" in result.lower() or "nomination" in result.lower()

    def test_keyword_matching_evm(self):
        result = _get_fallback_response("What is an EVM?")
        assert "EVM" in result or "Electronic Voting Machine" in result

    def test_default_fallback(self):
        result = _get_fallback_response("Tell me about the weather")
        assert result == FALLBACK_RESPONSES["default"]

    def test_case_insensitive_matching(self):
        result1 = _get_fallback_response("VOTING process")
        result2 = _get_fallback_response("voting process")
        assert result1 == result2


class TestStreamChatResponse:
    """Test the streaming chat response generator."""

    @pytest.mark.asyncio
    async def test_fallback_stream_produces_tokens(self):
        """Fallback mode should yield word tokens."""
        tokens = []
        async for token in stream_chat_response(
            system_prompt="You are a test assistant",
            message="Hello",
            history=[],
        ):
            tokens.append(token)

        assert len(tokens) > 0, "Should produce at least one token"
        full_response = "".join(tokens)
        assert len(full_response) > 10, "Response should be substantive"

    @pytest.mark.asyncio
    async def test_fallback_stream_vote_topic(self):
        """Voting-related questions should get vote-specific fallback."""
        tokens = []
        async for token in stream_chat_response(
            system_prompt="",
            message="How do I vote in elections?",
            history=[],
        ):
            tokens.append(token)

        full_response = "".join(tokens)
        assert "vote" in full_response.lower() or "polling" in full_response.lower()

    @pytest.mark.asyncio
    async def test_fallback_stream_register_topic(self):
        """Registration questions should get registration fallback."""
        tokens = []
        async for token in stream_chat_response(
            system_prompt="",
            message="How to register as voter?",
            history=[],
        ):
            tokens.append(token)

        full_response = "".join(tokens)
        assert "register" in full_response.lower() or "Form" in full_response

    @pytest.mark.asyncio
    async def test_stream_with_history(self):
        """Should handle conversation history without errors."""
        tokens = []
        async for token in stream_chat_response(
            system_prompt="",
            message="Tell me more",
            history=[
                {"role": "user", "content": "What is voting?"},
                {"role": "assistant", "content": "Voting is a fundamental right."},
            ],
        ):
            tokens.append(token)

        assert len(tokens) > 0
