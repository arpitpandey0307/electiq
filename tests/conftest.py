"""
Shared test fixtures for the ElectIQ test suite.

Provides reusable TestClient, mock data, and configuration
fixtures for consistent testing across all test modules.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import DataCache


@pytest.fixture(scope="session")
def client():
    """Provide a TestClient for the FastAPI application."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def cache():
    """Provide the DataCache singleton instance."""
    return DataCache.get_instance()


@pytest.fixture
def sample_chat_request():
    """Provide a valid chat request payload."""
    return {
        "role": "voter",
        "message": "How do I register to vote?",
        "history": [],
    }


@pytest.fixture
def sample_chat_with_history():
    """Provide a chat request with conversation history."""
    return {
        "role": "student",
        "message": "Tell me more about that",
        "history": [
            {"role": "user", "content": "What is voting?"},
            {"role": "assistant", "content": "Voting is the process of casting a ballot in an election."},
        ],
    }


@pytest.fixture
def all_roles():
    """Provide all valid user roles."""
    return ["voter", "candidate", "journalist", "student"]
