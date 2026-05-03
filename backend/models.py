"""
ElectIQ — Pydantic Models

Type-safe request and response models for all API endpoints.
Provides input validation, sanitization, and automatic API
documentation via FastAPI's OpenAPI integration.

All models use strict validation to prevent injection attacks
and enforce data integrity constraints.
"""

from __future__ import annotations

import html
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

__all__ = [
    "ChatRequest",
    "HealthResponse",
    "ChatSuggestionResponse",
    "QuizTopicSummary",
    "QuizTopicListResponse",
    "ErrorResponse",
    "SuggestionQueryParams",
]

# Allowed user roles — centralized for consistency
VALID_ROLES: frozenset[str] = frozenset(
    {"voter", "candidate", "journalist", "student"}
)


# ── Request Models ──


class ChatRequest(BaseModel):
    """
    Validated chat request with input sanitization.

    Attributes:
        role: User persona for contextualized responses.
        message: User's question (1–2000 characters, HTML-escaped).
        history: Recent conversation history (max 20 turns).
    """

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "role": "voter",
                    "message": "How do I register to vote?",
                    "history": [],
                }
            ]
        }
    }

    role: str = Field(
        default="voter",
        description="User persona for contextualized responses",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's question (1–2000 characters)",
    )
    history: list[dict[str, Any]] = Field(
        default_factory=list,
        max_length=20,
        description="Recent conversation history (max 20 turns)",
    )

    @field_validator("role", mode="before")
    @classmethod
    def normalize_and_validate_role(cls, v: Any) -> str:
        """Normalize role to lowercase and validate against allowed values."""
        if not isinstance(v, str):
            raise ValueError("Role must be a string")
        normalized = v.lower().strip()
        if normalized not in VALID_ROLES:
            raise ValueError(
                f"Role must be one of: {', '.join(sorted(VALID_ROLES))}"
            )
        return normalized

    @field_validator("message", mode="before")
    @classmethod
    def sanitize_message(cls, v: Any) -> str:
        """
        Strip whitespace and escape HTML to prevent XSS.

        This is a defense-in-depth measure that ensures user input
        is safe even if rendered in a web context.
        """
        if not isinstance(v, str):
            raise ValueError("Message must be a string")
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message cannot be empty or whitespace only")
        return html.escape(stripped)

    @model_validator(mode="after")
    def validate_history_entries(self) -> ChatRequest:
        """Ensure history entries have required 'role' and 'content' keys."""
        for i, entry in enumerate(self.history):
            if "role" not in entry or "content" not in entry:
                raise ValueError(
                    f"History entry {i} must have 'role' and 'content' keys"
                )
        return self


class SuggestionQueryParams(BaseModel):
    """Validated query parameters for the chat suggestions endpoint."""

    role: str = Field(
        default="voter",
        description="User persona for suggested questions",
    )

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, v: Any) -> str:
        """Normalize and validate role, defaulting to 'voter' for invalid."""
        if not isinstance(v, str):
            return "voter"
        normalized = v.lower().strip()
        return normalized if normalized in VALID_ROLES else "voter"


# ── Response Models ──


class HealthResponse(BaseModel):
    """
    Health check response for Cloud Run readiness and liveness probes.

    This model is used by Google Cloud Run to determine service health
    and by monitoring dashboards for uptime tracking.
    """

    status: str = Field(description="Service health status")
    service: str = Field(description="Service name")
    version: str = Field(description="Application version")
    gemini_configured: bool = Field(
        description="Whether the Google Gemini API key is configured"
    )


class ChatSuggestionResponse(BaseModel):
    """Suggested starter questions for a given role."""

    suggestions: list[str] = Field(
        description="List of suggested questions"
    )


class QuizTopicSummary(BaseModel):
    """Summary of a quiz topic for the topic selector UI."""

    id: str = Field(description="Unique topic identifier")
    title: str = Field(description="Display name of the topic")
    icon: str = Field(description="Emoji icon for the topic")
    question_count: int = Field(
        ge=1, description="Number of questions in this topic"
    )


class QuizTopicListResponse(BaseModel):
    """List of all available quiz topics."""

    topics: list[QuizTopicSummary] = Field(
        description="Available quiz topics"
    )


class ErrorResponse(BaseModel):
    """
    Standardized error response following RFC 7807 problem details.

    Returned for all 4xx and 5xx responses to provide consistent
    error information to API consumers.
    """

    detail: str = Field(description="Human-readable error message")
    error_code: str = Field(
        default="UNKNOWN_ERROR",
        description="Machine-readable error code for client handling",
    )
