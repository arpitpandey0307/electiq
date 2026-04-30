"""
Model Validation Tests — Verify Pydantic models enforce constraints.

Tests input validation rules, sanitization logic, and default values
for all request/response models.
"""

import pytest
from pydantic import ValidationError
from backend.models import ChatRequest, HealthResponse, QuizTopicSummary


class TestChatRequestModel:
    """Validate ChatRequest input constraints."""

    def test_valid_request(self):
        """Well-formed request should pass validation."""
        req = ChatRequest(
            role="voter",
            message="How do I vote?",
            history=[],
        )
        assert req.role == "voter"
        assert req.message == "How do I vote?"

    def test_default_role(self):
        """Role should default to 'voter' when omitted."""
        req = ChatRequest(message="test")
        assert req.role == "voter"

    def test_valid_roles(self):
        """All four valid roles should be accepted."""
        for role in ["voter", "candidate", "journalist", "student"]:
            req = ChatRequest(role=role, message="test")
            assert req.role == role

    def test_invalid_role_rejected(self):
        """Invalid role values should raise ValidationError."""
        with pytest.raises(ValidationError):
            ChatRequest(role="admin", message="test")

    def test_empty_message_rejected(self):
        """Empty messages should raise ValidationError."""
        with pytest.raises(ValidationError):
            ChatRequest(role="voter", message="")

    def test_whitespace_only_message_rejected(self):
        """Whitespace-only messages should be rejected after strip."""
        with pytest.raises(ValidationError):
            ChatRequest(role="voter", message="   ")

    def test_oversized_message_rejected(self):
        """Messages over 2000 characters should be rejected."""
        with pytest.raises(ValidationError):
            ChatRequest(role="voter", message="x" * 2001)

    def test_max_length_message_accepted(self):
        """Message at exactly 2000 characters should be accepted."""
        req = ChatRequest(role="voter", message="x" * 2000)
        assert len(req.message) == 2000

    def test_html_sanitization(self):
        """HTML entities in messages should be escaped."""
        req = ChatRequest(
            role="voter",
            message="<script>alert('xss')</script>",
        )
        assert "<script>" not in req.message
        assert "&lt;script&gt;" in req.message

    def test_role_normalization(self):
        """Roles should be normalized to lowercase."""
        req = ChatRequest(role="Voter", message="test")
        assert req.role == "voter"

    def test_empty_history_default(self):
        """History should default to empty list."""
        req = ChatRequest(message="test")
        assert req.history == []


class TestHealthResponseModel:
    """Validate HealthResponse output schema."""

    def test_valid_response(self):
        """Well-formed health response should serialize correctly."""
        resp = HealthResponse(
            status="healthy",
            service="ElectIQ",
            version="1.0.0",
            gemini_configured=True,
        )
        data = resp.model_dump()
        assert data["status"] == "healthy"
        assert data["gemini_configured"] is True

    def test_serialization_roundtrip(self):
        """Model should survive JSON serialization roundtrip."""
        resp = HealthResponse(
            status="healthy",
            service="ElectIQ",
            version="1.0.0",
            gemini_configured=False,
        )
        json_str = resp.model_dump_json()
        restored = HealthResponse.model_validate_json(json_str)
        assert restored.status == "healthy"


class TestQuizTopicSummaryModel:
    """Validate QuizTopicSummary schema."""

    def test_valid_topic(self):
        """Well-formed topic summary should pass validation."""
        topic = QuizTopicSummary(
            id="voter-registration",
            title="Voter Registration",
            icon="📋",
            question_count=5,
        )
        assert topic.question_count == 5

    def test_serialization(self):
        """Topic should serialize to dict with all fields."""
        topic = QuizTopicSummary(
            id="test", title="Test", icon="🧪", question_count=3
        )
        data = topic.model_dump()
        assert set(data.keys()) == {"id", "title", "icon", "question_count"}
