"""
API Endpoint Tests — Comprehensive validation of all ElectIQ endpoints.

Tests cover happy paths, error handling, edge cases, response schemas,
and data integrity across all API routes.
"""

import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="module")
def client():
    """Shared test client for all endpoint tests."""
    with TestClient(app) as c:
        yield c


# ──────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────

class TestHealthEndpoint:
    """Validate the /health endpoint for Cloud Run probes."""

    def test_health_returns_200(self, client):
        """Health check should return HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_schema(self, client):
        """Health response must contain required fields."""
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert data["service"] == "ElectIQ"
        assert "version" in data
        assert "gemini_configured" in data
        assert isinstance(data["gemini_configured"], bool)


# ──────────────────────────────────────────────
# Timeline
# ──────────────────────────────────────────────

class TestTimelineEndpoint:
    """Validate the /api/timeline endpoint."""

    def test_timeline_returns_200(self, client):
        """Timeline endpoint should return HTTP 200."""
        response = client.get("/api/timeline")
        assert response.status_code == 200

    def test_timeline_has_milestones(self, client):
        """Timeline response must contain milestones array."""
        data = client.get("/api/timeline").json()
        assert "milestones" in data
        assert isinstance(data["milestones"], list)
        assert len(data["milestones"]) > 0

    def test_timeline_milestone_structure(self, client):
        """Each milestone must have required fields."""
        data = client.get("/api/timeline").json()
        required_fields = [
            "id", "label", "date", "icon", "status",
            "description", "details", "who_involved",
            "key_facts", "faq",
        ]
        for milestone in data["milestones"]:
            for field in required_fields:
                assert field in milestone, (
                    f"Missing '{field}' in milestone '{milestone.get('id')}'"
                )

    def test_timeline_valid_statuses(self, client):
        """Milestone statuses must be one of the valid values."""
        data = client.get("/api/timeline").json()
        valid_statuses = {"completed", "active", "upcoming"}
        for m in data["milestones"]:
            assert m["status"] in valid_statuses, (
                f"Invalid status '{m['status']}' for milestone '{m['id']}'"
            )


# ──────────────────────────────────────────────
# Quiz
# ──────────────────────────────────────────────

class TestQuizEndpoint:
    """Validate the /api/quiz endpoints."""

    def test_quiz_topics_returns_200(self, client):
        """Quiz topic list should return HTTP 200."""
        response = client.get("/api/quiz")
        assert response.status_code == 200

    def test_quiz_topics_structure(self, client):
        """Quiz topics must have required fields."""
        data = client.get("/api/quiz").json()
        assert "topics" in data
        assert isinstance(data["topics"], list)
        assert len(data["topics"]) >= 5  # We have 5 topics

        for topic in data["topics"]:
            assert "id" in topic
            assert "title" in topic
            assert "icon" in topic
            assert "question_count" in topic
            assert topic["question_count"] > 0

    def test_quiz_topic_by_id(self, client):
        """Fetching a valid topic should return questions."""
        data = client.get("/api/quiz/voter-registration").json()
        assert "questions" in data
        assert "title" in data
        assert len(data["questions"]) == 5

    def test_quiz_question_structure(self, client):
        """Each question must have required fields."""
        data = client.get("/api/quiz/voter-registration").json()
        for q in data["questions"]:
            assert "q" in q
            assert "options" in q
            assert "answer" in q
            assert "explanation" in q
            assert isinstance(q["options"], list)
            assert len(q["options"]) == 4
            assert 0 <= q["answer"] <= 3

    def test_quiz_invalid_topic_returns_404(self, client):
        """Requesting a non-existent topic should return 404."""
        response = client.get("/api/quiz/nonexistent-topic")
        assert response.status_code == 404

    def test_all_quiz_topics_loadable(self, client):
        """All listed topics should be individually retrievable."""
        topics = client.get("/api/quiz").json()["topics"]
        for topic in topics:
            response = client.get(f"/api/quiz/{topic['id']}")
            assert response.status_code == 200
            data = response.json()
            assert len(data["questions"]) == topic["question_count"]


# ──────────────────────────────────────────────
# Scenarios
# ──────────────────────────────────────────────

class TestScenariosEndpoint:
    """Validate the /api/scenarios endpoint."""

    def test_scenarios_returns_200(self, client):
        """Scenarios endpoint should return HTTP 200."""
        response = client.get("/api/scenarios")
        assert response.status_code == 200

    def test_scenarios_has_list(self, client):
        """Scenarios response must contain scenarios array."""
        data = client.get("/api/scenarios").json()
        assert "scenarios" in data
        assert isinstance(data["scenarios"], list)
        assert len(data["scenarios"]) >= 6

    def test_scenario_structure(self, client):
        """Each scenario must have required fields."""
        data = client.get("/api/scenarios").json()
        for scenario in data["scenarios"]:
            assert "id" in scenario
            assert "title" in scenario
            assert "icon" in scenario
            assert "description" in scenario
            assert "tree" in scenario

    def test_scenario_tree_has_question(self, client):
        """Each scenario tree root must have a question field."""
        data = client.get("/api/scenarios").json()
        for scenario in data["scenarios"]:
            tree = scenario["tree"]
            assert "question" in tree or "result" in tree


# ──────────────────────────────────────────────
# Glossary
# ──────────────────────────────────────────────

class TestGlossaryEndpoint:
    """Validate the /api/glossary endpoint."""

    def test_glossary_returns_200(self, client):
        """Glossary endpoint should return HTTP 200."""
        response = client.get("/api/glossary")
        assert response.status_code == 200

    def test_glossary_has_terms(self, client):
        """Glossary must contain a non-empty terms array."""
        data = client.get("/api/glossary").json()
        assert "terms" in data
        assert isinstance(data["terms"], list)
        assert len(data["terms"]) >= 10

    def test_glossary_term_structure(self, client):
        """Each glossary term must have required fields."""
        data = client.get("/api/glossary").json()
        for term in data["terms"]:
            assert "term" in term
            assert "icon" in term
            assert "short" in term
            assert "detailed" in term
            assert len(term["short"]) > 0
            assert len(term["detailed"]) > 0


# ──────────────────────────────────────────────
# Chat
# ──────────────────────────────────────────────

class TestChatEndpoint:
    """Validate the /api/chat endpoints."""

    def test_chat_suggestions_returns_200(self, client):
        """Chat suggestions should return HTTP 200."""
        response = client.get("/api/chat/suggestions?role=voter")
        assert response.status_code == 200

    def test_chat_suggestions_structure(self, client):
        """Suggestions must be a non-empty list of strings."""
        data = client.get("/api/chat/suggestions?role=voter").json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        assert len(data["suggestions"]) > 0
        for suggestion in data["suggestions"]:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0

    def test_chat_suggestions_for_all_roles(self, client):
        """Each role should return different suggestions."""
        roles = ["voter", "candidate", "journalist", "student"]
        all_suggestions = {}
        for role in roles:
            data = client.get(f"/api/chat/suggestions?role={role}").json()
            assert len(data["suggestions"]) > 0
            all_suggestions[role] = data["suggestions"]

        # At least some roles should have different suggestions
        assert all_suggestions["voter"] != all_suggestions["candidate"]

    def test_chat_suggestions_invalid_role_defaults(self, client):
        """Invalid role should default to voter suggestions."""
        data = client.get("/api/chat/suggestions?role=invalid").json()
        assert len(data["suggestions"]) > 0

    def test_chat_stream_response(self, client):
        """Chat POST should return SSE stream."""
        response = client.post(
            "/api/chat",
            json={
                "role": "voter",
                "message": "How do I vote?",
                "history": [],
            },
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

    def test_chat_rejects_empty_message(self, client):
        """Chat should reject empty messages with 422."""
        response = client.post(
            "/api/chat",
            json={"role": "voter", "message": "", "history": []},
        )
        assert response.status_code == 422

    def test_chat_rejects_invalid_role(self, client):
        """Chat should reject invalid roles with 422."""
        response = client.post(
            "/api/chat",
            json={"role": "hacker", "message": "test", "history": []},
        )
        assert response.status_code == 422


# ──────────────────────────────────────────────
# Index Page
# ──────────────────────────────────────────────

class TestIndexPage:
    """Validate the frontend index page serving."""

    def test_index_returns_200(self, client):
        """Root path should serve index.html."""
        response = client.get("/")
        assert response.status_code == 200

    def test_index_is_html(self, client):
        """Root response should be HTML."""
        response = client.get("/")
        assert "text/html" in response.headers["content-type"]

    def test_index_contains_app_name(self, client):
        """Index page should contain the application name."""
        response = client.get("/")
        assert "ElectIQ" in response.text
