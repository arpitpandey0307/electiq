"""
Pydantic Model Tests for ElectIQ.

Tests all request/response models for validation constraints,
serialization, and edge cases.
"""

import pytest

from backend.models import (
    ChatRequest,
    HealthResponse,
    ChatSuggestionResponse,
    QuizTopicSummary,
    SuggestionQueryParams,
    ErrorResponse,
    VALID_ROLES,
)


class TestChatRequest:
    """ChatRequest model validation tests."""

    def test_valid_request(self):
        req = ChatRequest(role="voter", message="Hello")
        assert req.role == "voter"
        assert req.message == "Hello"
        assert req.history == []

    def test_default_role(self):
        req = ChatRequest(message="Hello")
        assert req.role == "voter"

    def test_role_case_insensitive(self):
        req = ChatRequest(role="VOTER", message="Hello")
        assert req.role == "voter"

    def test_role_stripped(self):
        req = ChatRequest(role="  candidate  ", message="Hello")
        assert req.role == "candidate"

    def test_invalid_role_raises(self):
        with pytest.raises(ValueError):
            ChatRequest(role="hacker", message="Hello")

    def test_message_sanitized(self):
        req = ChatRequest(role="voter", message="<b>bold</b>")
        assert "&lt;b&gt;" in req.message
        assert "<b>" not in req.message

    def test_empty_message_raises(self):
        with pytest.raises(ValueError):
            ChatRequest(role="voter", message="")

    def test_whitespace_message_raises(self):
        with pytest.raises(ValueError):
            ChatRequest(role="voter", message="   ")

    def test_oversized_message_raises(self):
        with pytest.raises(ValueError):
            ChatRequest(role="voter", message="A" * 2001)

    def test_max_length_message_accepted(self):
        req = ChatRequest(role="voter", message="A" * 2000)
        assert len(req.message) == 2000

    def test_history_default_empty(self):
        req = ChatRequest(role="voter", message="Hello")
        assert req.history == []

    def test_history_with_valid_entries(self):
        req = ChatRequest(
            role="voter",
            message="Hello",
            history=[
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello!"},
            ],
        )
        assert len(req.history) == 2

    def test_history_with_invalid_entry_raises(self):
        with pytest.raises(ValueError):
            ChatRequest(
                role="voter",
                message="Hello",
                history=[{"invalid": "entry"}],
            )

    def test_all_valid_roles(self):
        for role in VALID_ROLES:
            req = ChatRequest(role=role, message="Test")
            assert req.role == role

    def test_unicode_message(self):
        req = ChatRequest(role="voter", message="मतदान कैसे करें?")
        assert "मतदान" in req.message

    def test_special_characters_escaped(self):
        req = ChatRequest(role="voter", message='Hello & "world" <test>')
        assert "&amp;" in req.message
        assert "&lt;" in req.message
        assert "&gt;" in req.message
        assert "&quot;" in req.message


class TestSuggestionQueryParams:
    """SuggestionQueryParams validation tests."""

    def test_valid_role(self):
        params = SuggestionQueryParams(role="voter")
        assert params.role == "voter"

    def test_invalid_role_defaults_to_voter(self):
        params = SuggestionQueryParams(role="invalid")
        assert params.role == "voter"

    def test_empty_role_defaults_to_voter(self):
        params = SuggestionQueryParams(role="")
        assert params.role == "voter"

    def test_case_insensitive(self):
        params = SuggestionQueryParams(role="JOURNALIST")
        assert params.role == "journalist"


class TestHealthResponse:
    """HealthResponse model tests."""

    def test_serialization(self):
        resp = HealthResponse(
            status="healthy",
            service="ElectIQ",
            version="1.0.0",
            gemini_configured=True,
        )
        data = resp.model_dump()
        assert data["status"] == "healthy"
        assert data["gemini_configured"] is True

    def test_roundtrip(self):
        original = {
            "status": "healthy",
            "service": "ElectIQ",
            "version": "1.0.0",
            "gemini_configured": False,
        }
        resp = HealthResponse(**original)
        assert resp.model_dump() == original


class TestQuizTopicSummary:
    """QuizTopicSummary model tests."""

    def test_valid_summary(self):
        summary = QuizTopicSummary(
            id="voting", title="Voting Process", icon="🗳️", question_count=5
        )
        assert summary.question_count == 5

    def test_zero_question_count_raises(self):
        with pytest.raises(ValueError):
            QuizTopicSummary(
                id="test", title="Test", icon="📝", question_count=0
            )


class TestErrorResponse:
    """ErrorResponse model tests."""

    def test_default_error_code(self):
        err = ErrorResponse(detail="Something went wrong")
        assert err.error_code == "UNKNOWN_ERROR"

    def test_custom_error_code(self):
        err = ErrorResponse(detail="Too many requests", error_code="RATE_LIMIT_EXCEEDED")
        assert err.error_code == "RATE_LIMIT_EXCEEDED"
