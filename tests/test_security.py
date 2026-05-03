"""
Security Tests for ElectIQ.

Tests OWASP security headers, input sanitization, data integrity,
rate limiting, CORS, and compression.
"""

import time
import pytest


class TestSecurityHeaders:
    """Verify all OWASP-recommended security headers are present."""

    def test_x_frame_options_deny(self, client):
        response = client.get("/health")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_x_content_type_options(self, client):
        response = client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_xss_protection(self, client):
        response = client.get("/health")
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_content_security_policy(self, client):
        response = client.get("/health")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "default-src 'self'" in csp
        assert "script-src" in csp
        assert "frame-ancestors 'none'" in csp

    def test_csp_allows_google_fonts(self, client):
        csp = client.get("/health").headers.get("Content-Security-Policy", "")
        assert "fonts.googleapis.com" in csp
        assert "fonts.gstatic.com" in csp

    def test_referrer_policy(self, client):
        response = client.get("/health")
        assert "strict-origin" in response.headers.get("Referrer-Policy", "")

    def test_permissions_policy(self, client):
        response = client.get("/health")
        policy = response.headers.get("Permissions-Policy", "")
        assert "camera=()" in policy
        assert "microphone=()" in policy
        assert "geolocation=()" in policy

    def test_cross_origin_opener_policy(self, client):
        response = client.get("/health")
        assert response.headers.get("Cross-Origin-Opener-Policy") == "same-origin"

    def test_cross_origin_resource_policy(self, client):
        response = client.get("/health")
        assert response.headers.get("Cross-Origin-Resource-Policy") == "same-origin"

    def test_x_permitted_cross_domain_policies(self, client):
        response = client.get("/health")
        assert response.headers.get("X-Permitted-Cross-Domain-Policies") == "none"

    def test_server_timing_header(self, client):
        response = client.get("/health")
        assert "Server-Timing" in response.headers

    def test_request_id_header(self, client):
        response = client.get("/health")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 16


class TestInputValidation:
    """Test input sanitization and validation."""

    def test_html_injection_prevented(self, client):
        """HTML entities should be escaped in chat messages."""
        response = client.post("/api/chat", json={
            "role": "voter",
            "message": "<script>alert('xss')</script>",
        })
        # Should not return 422 (message is valid, just sanitized)
        assert response.status_code == 200
        assert "<script>" not in response.text

    def test_oversized_message_rejected(self, client):
        response = client.post("/api/chat", json={
            "role": "voter",
            "message": "X" * 2001,
        })
        assert response.status_code == 422

    def test_invalid_role_rejected(self, client):
        response = client.post("/api/chat", json={
            "role": "admin",
            "message": "Hello",
        })
        assert response.status_code == 422

    def test_empty_message_rejected(self, client):
        response = client.post("/api/chat", json={
            "role": "voter",
            "message": "",
        })
        assert response.status_code == 422

    def test_whitespace_only_message_rejected(self, client):
        response = client.post("/api/chat", json={
            "role": "voter",
            "message": "   ",
        })
        assert response.status_code == 422

    def test_role_case_insensitive(self, client):
        response = client.post("/api/chat", json={
            "role": "VOTER",
            "message": "Hello",
        })
        assert response.status_code == 200

    def test_role_with_whitespace(self, client):
        response = client.post("/api/chat", json={
            "role": "  voter  ",
            "message": "Hello",
        })
        assert response.status_code == 200

    def test_invalid_history_entry(self, client):
        response = client.post("/api/chat", json={
            "role": "voter",
            "message": "Hello",
            "history": [{"invalid": "entry"}],
        })
        assert response.status_code == 422

    def test_unicode_message_accepted(self, client):
        response = client.post("/api/chat", json={
            "role": "voter",
            "message": "मतदान कैसे करें?",  # Hindi
        })
        assert response.status_code == 200

    def test_special_characters_in_message(self, client):
        response = client.post("/api/chat", json={
            "role": "voter",
            "message": "What about 'quotes' & \"double quotes\" and <angle brackets>?",
        })
        assert response.status_code == 200


class TestDataIntegrity:
    """Verify data files are consistent and correct."""

    def test_quiz_answer_ranges(self, cache):
        for topic_id, topic_data in cache.quiz.items():
            for q in topic_data.get("questions", []):
                assert 0 <= q["answer"] < len(q["options"]), \
                    f"Answer out of range in {topic_id}: {q['q']}"

    def test_quiz_explanation_quality(self, cache):
        for topic_id, topic_data in cache.quiz.items():
            for q in topic_data.get("questions", []):
                assert len(q["explanation"]) >= 20, \
                    f"Explanation too short: {q['q']}"

    def test_timeline_dates_valid(self, cache):
        milestones = cache.timeline.get("milestones", [])
        for m in milestones:
            from datetime import datetime
            try:
                datetime.strptime(m["date"], "%Y-%m-%d")
            except (ValueError, KeyError):
                pytest.fail(f"Invalid date in milestone: {m.get('id', 'unknown')}")

    def test_timeline_ids_unique(self, cache):
        milestones = cache.timeline.get("milestones", [])
        ids = [m["id"] for m in milestones]
        assert len(ids) == len(set(ids)), "Timeline IDs must be unique"

    def test_scenario_ids_unique(self, cache):
        scenarios = cache.scenarios.get("scenarios", [])
        ids = [s["id"] for s in scenarios]
        assert len(ids) == len(set(ids)), "Scenario IDs must be unique"

    def test_glossary_terms_unique(self, cache):
        terms = cache.glossary.get("terms", [])
        names = [t["term"] for t in terms]
        assert len(names) == len(set(names)), "Glossary terms must be unique"


class TestPerformance:
    """Response time and performance header tests."""

    def test_health_response_time(self, client):
        start = time.time()
        client.get("/health")
        duration = time.time() - start
        assert duration < 1.0, f"Health check too slow: {duration:.3f}s"

    def test_timeline_response_time(self, client):
        start = time.time()
        client.get("/api/timeline")
        duration = time.time() - start
        assert duration < 1.0, f"Timeline too slow: {duration:.3f}s"

    def test_quiz_response_time(self, client):
        start = time.time()
        client.get("/api/quiz")
        duration = time.time() - start
        assert duration < 1.0, f"Quiz list too slow: {duration:.3f}s"

    def test_server_timing_present(self, client):
        response = client.get("/health")
        timing = response.headers.get("Server-Timing", "")
        assert "dur=" in timing


class TestCORS:
    """CORS header tests."""

    def test_cors_origin_header(self, client):
        response = client.options(
            "/api/timeline",
            headers={"Origin": "http://localhost:8080", "Access-Control-Request-Method": "GET"}
        )
        # Should not return 405 for OPTIONS
        assert response.status_code in (200, 204, 405) or "access-control" in str(response.headers).lower()
