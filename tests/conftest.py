"""
Shared test fixtures and configuration for ElectIQ test suite.

Sets a high rate limit for the test environment to prevent
rate-limiting from interfering with test execution.
"""

import os

# Set high rate limit BEFORE importing the app (config reads env at import)
os.environ["RATE_LIMIT_REQUESTS"] = "1000"
os.environ["APP_ENV"] = "development"

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture(scope="module")
def client():
    """
    Create a shared TestClient for the FastAPI application.

    Uses module scope to reuse the client across all tests in
    a module, improving test execution speed.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_chat_request():
    """Return a valid chat request payload."""
    return {
        "role": "voter",
        "message": "How do I register to vote?",
        "history": [],
    }


@pytest.fixture
def sample_chat_with_history():
    """Return a chat request with conversation history."""
    return {
        "role": "student",
        "message": "Tell me more about that",
        "history": [
            {"role": "user", "content": "What is an EVM?"},
            {"role": "assistant", "content": "An EVM is an Electronic Voting Machine..."},
        ],
    }
