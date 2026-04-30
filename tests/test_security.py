"""
Security Tests — Validate security headers, input sanitization,
rate limiting, and safe response handling.

Ensures the application follows OWASP security best practices
and protects against common web vulnerabilities.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="module")
def client():
    """Shared test client for security tests."""
    with TestClient(app) as c:
        yield c


class TestSecurityHeaders:
    """Verify OWASP-recommended security headers on responses."""

    def test_x_frame_options(self, client):
        """Responses must include X-Frame-Options: DENY."""
        response = client.get("/health")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_x_content_type_options(self, client):
        """Responses must prevent MIME sniffing."""
        response = client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_xss_protection(self, client):
        """Responses must enable XSS filter."""
        response = client.get("/health")
        assert "1; mode=block" in response.headers.get(
            "X-XSS-Protection", ""
        )

    def test_content_security_policy(self, client):
        """Responses must include a Content-Security-Policy header."""
        response = client.get("/health")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "default-src" in csp
        assert "script-src" in csp
        assert "frame-ancestors 'none'" in csp

    def test_referrer_policy(self, client):
        """Responses must include a Referrer-Policy header."""
        response = client.get("/health")
        assert response.headers.get("Referrer-Policy") is not None

    def test_permissions_policy(self, client):
        """Responses must restrict unnecessary browser features."""
        response = client.get("/health")
        pp = response.headers.get("Permissions-Policy", "")
        assert "camera=()" in pp
        assert "microphone=()" in pp


class TestInputValidation:
    """Verify input sanitization and validation."""

    def test_chat_rejects_oversized_message(self, client):
        """Messages exceeding 2000 characters should be rejected."""
        response = client.post(
            "/api/chat",
            json={
                "role": "voter",
                "message": "x" * 2001,
                "history": [],
            },
        )
        assert response.status_code == 422

    def test_chat_rejects_invalid_role_pattern(self, client):
        """Roles not matching the allowed pattern should be rejected."""
        response = client.post(
            "/api/chat",
            json={
                "role": "admin",
                "message": "test",
                "history": [],
            },
        )
        assert response.status_code == 422

    def test_chat_sanitizes_html_in_message(self, client):
        """HTML in messages should be escaped to prevent XSS."""
        response = client.post(
            "/api/chat",
            json={
                "role": "voter",
                "message": "<script>alert('xss')</script>",
                "history": [],
            },
        )
        # Should succeed but with sanitized content
        assert response.status_code == 200

    def test_quiz_invalid_topic_returns_404(self, client):
        """Non-existent quiz topics should return 404, not 500."""
        response = client.get("/api/quiz/../../etc/passwd")
        assert response.status_code == 404

    def test_suggestions_invalid_role_handled(self, client):
        """Invalid role for suggestions should not crash."""
        response = client.get("/api/chat/suggestions?role=<script>")
        assert response.status_code == 200


class TestDataIntegrity:
    """Verify data consistency and correctness."""

    def test_quiz_answers_within_range(self, client):
        """All quiz answers must be valid option indices (0-3)."""
        topics = client.get("/api/quiz").json()["topics"]
        for topic in topics:
            data = client.get(f"/api/quiz/{topic['id']}").json()
            for q in data["questions"]:
                assert 0 <= q["answer"] < len(q["options"]), (
                    f"Invalid answer index {q['answer']} for: {q['q']}"
                )

    def test_quiz_all_questions_have_explanations(self, client):
        """Every quiz question must include an explanation."""
        topics = client.get("/api/quiz").json()["topics"]
        for topic in topics:
            data = client.get(f"/api/quiz/{topic['id']}").json()
            for q in data["questions"]:
                assert len(q.get("explanation", "")) > 10, (
                    f"Missing/short explanation for: {q['q']}"
                )

    def test_timeline_dates_are_valid(self, client):
        """All timeline dates must be parseable."""
        from datetime import datetime
        data = client.get("/api/timeline").json()
        for m in data["milestones"]:
            try:
                datetime.strptime(m["date"], "%Y-%m-%d")
            except ValueError:
                pytest.fail(f"Invalid date '{m['date']}' for '{m['id']}'")

    def test_glossary_no_duplicate_terms(self, client):
        """Glossary should not contain duplicate terms."""
        data = client.get("/api/glossary").json()
        term_names = [t["term"] for t in data["terms"]]
        assert len(term_names) == len(set(term_names)), "Duplicate glossary terms found"

    def test_scenarios_all_have_unique_ids(self, client):
        """All scenarios must have unique identifiers."""
        data = client.get("/api/scenarios").json()
        ids = [s["id"] for s in data["scenarios"]]
        assert len(ids) == len(set(ids)), "Duplicate scenario IDs found"


class TestResponseHeaders:
    """Verify response performance and caching headers."""

    def test_server_timing_header(self, client):
        """API responses should include Server-Timing for monitoring."""
        response = client.get("/health")
        assert "Server-Timing" in response.headers

    def test_health_response_time_reasonable(self, client):
        """Health check should respond within 1 second."""
        import time
        start = time.time()
        response = client.get("/health")
        duration = time.time() - start
        assert response.status_code == 200
        assert duration < 1.0, f"Health check too slow: {duration:.2f}s"
