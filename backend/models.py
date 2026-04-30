"""
ElectIQ — Pydantic Models

Type-safe request and response models for all API endpoints.
Provides input validation, sanitization, and automatic API
documentation via FastAPI's OpenAPI integration.
"""

from pydantic import BaseModel, Field, field_validator
import html


# ── Request Models ──

class ChatRequest(BaseModel):
    """Validated chat request with input sanitization."""

    role: str = Field(
        default="voter",
        description="User persona for contextualized responses",
    )
    message: str = Field(
        ...,
        max_length=2000,
        description="User's question (1–2000 characters)",
    )
    history: list[dict] = Field(
        default_factory=list,
        max_length=20,
        description="Recent conversation history (max 20 turns)",
    )

    @field_validator("role", mode="before")
    @classmethod
    def normalize_and_validate_role(cls, v: str) -> str:
        """Normalize role to lowercase and validate against allowed values."""
        normalized = v.lower().strip() if isinstance(v, str) else v
        valid_roles = {"voter", "candidate", "journalist", "student"}
        if normalized not in valid_roles:
            raise ValueError(
                f"Role must be one of: {', '.join(sorted(valid_roles))}"
            )
        return normalized

    @field_validator("message", mode="before")
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        """Strip whitespace and escape HTML to prevent XSS."""
        if not isinstance(v, str):
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message cannot be empty or whitespace only")
        return html.escape(stripped)


# ── Response Models ──

class HealthResponse(BaseModel):
    """Health check response for Cloud Run readiness probes."""

    status: str = Field(description="Service health status")
    service: str = Field(description="Service name")
    version: str = Field(description="Application version")
    gemini_configured: bool = Field(
        description="Whether the Gemini API key is configured"
    )


class ChatSuggestionResponse(BaseModel):
    """Suggested starter questions for a given role."""

    suggestions: list[str] = Field(
        description="List of suggested questions"
    )


class QuizTopicSummary(BaseModel):
    """Summary of a quiz topic for the topic selector."""

    id: str
    title: str
    icon: str
    question_count: int


class QuizTopicListResponse(BaseModel):
    """List of all available quiz topics."""

    topics: list[QuizTopicSummary]


class ErrorResponse(BaseModel):
    """Standardized error response."""

    detail: str = Field(description="Human-readable error message")
    error_code: str = Field(
        default="UNKNOWN_ERROR",
        description="Machine-readable error code",
    )
