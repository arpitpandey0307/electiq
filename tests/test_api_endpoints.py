"""
API Endpoint Tests for ElectIQ.

Tests all API endpoints covering happy paths, error cases,
response structure validation, and content correctness.
"""

import json
import pytest


class TestHealthEndpoint:
    """Health check endpoint tests."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_schema(self, client):
        data = client.get("/health").json()
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "gemini_configured" in data

    def test_health_status_healthy(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert data["service"] == "ElectIQ"

    def test_health_version_format(self, client):
        data = client.get("/health").json()
        parts = data["version"].split(".")
        assert len(parts) == 3, "Version should be semver x.y.z"

    def test_health_gemini_configured_is_bool(self, client):
        data = client.get("/health").json()
        assert isinstance(data["gemini_configured"], bool)


class TestIndexPage:
    """Root page serving tests."""

    def test_index_returns_html(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_index_contains_app_name(self, client):
        response = client.get("/")
        assert "ElectIQ" in response.text

    def test_index_has_lang_attribute(self, client):
        response = client.get("/")
        assert 'lang="en"' in response.text

    def test_index_has_meta_description(self, client):
        response = client.get("/")
        assert 'meta name="description"' in response.text

    def test_index_has_skip_link(self, client):
        response = client.get("/")
        assert "skip-link" in response.text

    def test_index_has_main_content(self, client):
        response = client.get("/")
        assert 'id="main-content"' in response.text

    def test_index_has_aria_live_region(self, client):
        response = client.get("/")
        assert 'aria-live="polite"' in response.text


class TestTimelineEndpoint:
    """Timeline API tests."""

    def test_timeline_returns_200(self, client):
        response = client.get("/api/timeline")
        assert response.status_code == 200

    def test_timeline_has_milestones(self, client):
        data = client.get("/api/timeline").json()
        assert "milestones" in data
        assert len(data["milestones"]) > 0

    def test_timeline_milestone_structure(self, client):
        milestone = client.get("/api/timeline").json()["milestones"][0]
        required_fields = ["id", "label", "date", "icon", "status"]
        for field in required_fields:
            assert field in milestone, f"Missing field: {field}"

    def test_timeline_milestone_statuses(self, client):
        valid_statuses = {"completed", "active", "upcoming"}
        milestones = client.get("/api/timeline").json()["milestones"]
        for m in milestones:
            assert m["status"] in valid_statuses, f"Invalid status: {m['status']}"

    def test_timeline_has_cache_control(self, client):
        response = client.get("/api/timeline")
        assert "Cache-Control" in response.headers

    def test_timeline_has_vary_header(self, client):
        response = client.get("/api/timeline")
        assert "Vary" in response.headers

    def test_timeline_milestone_has_details(self, client):
        milestone = client.get("/api/timeline").json()["milestones"][0]
        assert "details" in milestone or "description" in milestone

    def test_timeline_milestone_has_key_facts(self, client):
        milestone = client.get("/api/timeline").json()["milestones"][0]
        assert "key_facts" in milestone
        assert isinstance(milestone["key_facts"], list)


class TestQuizEndpoint:
    """Quiz API tests."""

    def test_quiz_topics_list_returns_200(self, client):
        response = client.get("/api/quiz")
        assert response.status_code == 200

    def test_quiz_topics_has_topics(self, client):
        data = client.get("/api/quiz").json()
        assert "topics" in data
        assert len(data["topics"]) > 0

    def test_quiz_topic_summary_structure(self, client):
        topic = client.get("/api/quiz").json()["topics"][0]
        assert "id" in topic
        assert "title" in topic
        assert "icon" in topic
        assert "question_count" in topic
        assert topic["question_count"] > 0

    def test_quiz_per_topic_returns_200(self, client):
        topics = client.get("/api/quiz").json()["topics"]
        for topic in topics:
            response = client.get(f"/api/quiz/{topic['id']}")
            assert response.status_code == 200, f"Failed for topic: {topic['id']}"

    def test_quiz_question_structure(self, client):
        topics = client.get("/api/quiz").json()["topics"]
        data = client.get(f"/api/quiz/{topics[0]['id']}").json()
        assert "questions" in data
        q = data["questions"][0]
        assert "q" in q
        assert "options" in q
        assert "answer" in q
        assert "explanation" in q

    def test_quiz_answer_in_range(self, client):
        """Verify all quiz answers point to valid option indices."""
        topics = client.get("/api/quiz").json()["topics"]
        for topic in topics:
            data = client.get(f"/api/quiz/{topic['id']}").json()
            for q in data["questions"]:
                assert 0 <= q["answer"] < len(q["options"]), \
                    f"Answer {q['answer']} out of range for: {q['q']}"

    def test_quiz_invalid_topic_returns_404(self, client):
        response = client.get("/api/quiz/nonexistent-topic")
        assert response.status_code == 404

    def test_quiz_has_cache_control(self, client):
        topics = client.get("/api/quiz").json()["topics"]
        response = client.get(f"/api/quiz/{topics[0]['id']}")
        assert "Cache-Control" in response.headers

    def test_quiz_explanations_not_empty(self, client):
        topics = client.get("/api/quiz").json()["topics"]
        for topic in topics:
            data = client.get(f"/api/quiz/{topic['id']}").json()
            for q in data["questions"]:
                assert len(q["explanation"]) > 10, \
                    f"Empty/short explanation for: {q['q']}"


class TestScenarioEndpoint:
    """Scenario API tests."""

    def test_scenarios_returns_200(self, client):
        response = client.get("/api/scenarios")
        assert response.status_code == 200

    def test_scenarios_has_scenarios(self, client):
        data = client.get("/api/scenarios").json()
        assert "scenarios" in data
        assert len(data["scenarios"]) > 0

    def test_scenario_structure(self, client):
        scenario = client.get("/api/scenarios").json()["scenarios"][0]
        assert "id" in scenario
        assert "title" in scenario
        assert "icon" in scenario
        assert "tree" in scenario

    def test_scenario_ids_unique(self, client):
        scenarios = client.get("/api/scenarios").json()["scenarios"]
        ids = [s["id"] for s in scenarios]
        assert len(ids) == len(set(ids)), "Scenario IDs must be unique"

    def test_scenario_tree_has_question(self, client):
        scenario = client.get("/api/scenarios").json()["scenarios"][0]
        tree = scenario["tree"]
        assert "question" in tree or "result" in tree

    def test_scenarios_has_cache_control(self, client):
        response = client.get("/api/scenarios")
        assert "Cache-Control" in response.headers


class TestGlossaryEndpoint:
    """Glossary API tests."""

    def test_glossary_returns_200(self, client):
        response = client.get("/api/glossary")
        assert response.status_code == 200

    def test_glossary_has_terms(self, client):
        data = client.get("/api/glossary").json()
        assert "terms" in data
        assert len(data["terms"]) > 0

    def test_glossary_term_structure(self, client):
        term = client.get("/api/glossary").json()["terms"][0]
        assert "term" in term
        assert "short" in term
        assert "icon" in term

    def test_glossary_terms_have_content(self, client):
        terms = client.get("/api/glossary").json()["terms"]
        for t in terms:
            assert len(t["short"]) > 5, f"Short desc too brief for: {t['term']}"

    def test_glossary_has_cache_control(self, client):
        response = client.get("/api/glossary")
        assert "Cache-Control" in response.headers


class TestChatEndpoint:
    """Chat API tests."""

    def test_chat_suggestions_returns_200(self, client, all_roles):
        for role in all_roles:
            response = client.get(f"/api/chat/suggestions?role={role}")
            assert response.status_code == 200

    def test_chat_suggestions_has_suggestions(self, client):
        data = client.get("/api/chat/suggestions?role=voter").json()
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0
        assert all(isinstance(s, str) for s in data["suggestions"])

    def test_chat_suggestions_default_role(self, client):
        """Should default to voter for invalid role."""
        data = client.get("/api/chat/suggestions?role=invalid").json()
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0

    def test_chat_sse_stream(self, client, sample_chat_request):
        response = client.post("/api/chat", json=sample_chat_request)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    def test_chat_sse_stream_has_tokens(self, client, sample_chat_request):
        response = client.post("/api/chat", json=sample_chat_request)
        content = response.text
        assert "data:" in content, "SSE stream should contain data events"

    def test_chat_sse_stream_has_done(self, client, sample_chat_request):
        response = client.post("/api/chat", json=sample_chat_request)
        assert '"done": true' in response.text or '"done":true' in response.text

    def test_chat_validation_empty_message(self, client):
        response = client.post("/api/chat", json={
            "role": "voter", "message": ""
        })
        assert response.status_code == 422

    def test_chat_validation_invalid_role(self, client):
        response = client.post("/api/chat", json={
            "role": "hacker", "message": "Hello"
        })
        assert response.status_code == 422

    def test_chat_validation_oversized_message(self, client):
        response = client.post("/api/chat", json={
            "role": "voter", "message": "A" * 2001
        })
        assert response.status_code == 422

    def test_chat_with_history(self, client, sample_chat_with_history):
        response = client.post("/api/chat", json=sample_chat_with_history)
        assert response.status_code == 200

    def test_chat_has_no_cache_header(self, client, sample_chat_request):
        response = client.post("/api/chat", json=sample_chat_request)
        cache_control = response.headers.get("Cache-Control", "")
        # SSE responses should not be cached
        assert "no-cache" in cache_control or "no-store" in cache_control or \
            response.headers.get("content-type", "").startswith("text/event-stream")
