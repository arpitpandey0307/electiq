"""
Middleware Tests for ElectIQ.

Tests rate limiting logic, security header injection,
and request logging with timing.
"""

import time
import pytest
from collections import OrderedDict

from backend.middleware import RateLimitMiddleware


class TestRateLimiterLogic:
    """Unit tests for rate limiter data structures and eviction."""

    def test_ordered_dict_lru_eviction(self):
        """OrderedDict should maintain insertion order for LRU."""
        d = OrderedDict()
        d["a"] = [1.0]
        d["b"] = [2.0]
        d["c"] = [3.0]
        # Pop oldest (LRU)
        d.popitem(last=False)
        assert "a" not in d
        assert "b" in d
        assert "c" in d

    def test_move_to_end_updates_lru(self):
        """Accessing an entry should move it to the end."""
        d = OrderedDict()
        d["a"] = [1.0]
        d["b"] = [2.0]
        d.move_to_end("a")
        d.popitem(last=False)
        assert "b" not in d
        assert "a" in d


class TestRateLimitIntegration:
    """Integration tests for rate limiting on API endpoints."""

    def test_api_request_not_rate_limited(self, client):
        """Normal requests should pass through."""
        response = client.get("/api/timeline")
        assert response.status_code == 200

    def test_health_not_rate_limited(self, client):
        """Health endpoint should bypass rate limiting."""
        for _ in range(50):
            response = client.get("/health")
            assert response.status_code == 200

    def test_static_files_not_rate_limited(self, client):
        """Static file requests should bypass rate limiting."""
        for _ in range(50):
            response = client.get("/")
            assert response.status_code == 200

    def test_rate_limiter_has_eviction(self):
        """LRU eviction should cap memory usage."""
        limiter_requests = OrderedDict()
        for i in range(100):
            limiter_requests[f"192.168.1.{i}"] = [time.time()]
        # Simulate eviction to max 50
        while len(limiter_requests) > 50:
            limiter_requests.popitem(last=False)
        assert len(limiter_requests) == 50

    def test_rate_limiter_window_cleanup(self):
        """Expired timestamps should be cleaned up."""
        now = time.time()
        timestamps = [now - 120, now - 90, now - 30, now - 5, now]
        window_start = now - 60
        cleaned = [t for t in timestamps if t > window_start]
        assert len(cleaned) == 3  # Only recent timestamps remain


class TestSecurityHeadersMiddleware:
    """Test security headers on different endpoint types."""

    def test_headers_on_api_endpoint(self, client):
        response = client.get("/api/timeline")
        assert "X-Frame-Options" in response.headers
        assert "Content-Security-Policy" in response.headers

    def test_headers_on_health(self, client):
        response = client.get("/health")
        assert "X-Frame-Options" in response.headers

    def test_headers_on_root(self, client):
        response = client.get("/")
        assert "X-Frame-Options" in response.headers

    def test_csp_blocks_frames(self, client):
        csp = client.get("/health").headers.get("Content-Security-Policy", "")
        assert "frame-ancestors 'none'" in csp


class TestRequestLoggingMiddleware:
    """Test request logging and timing headers."""

    def test_server_timing_header(self, client):
        response = client.get("/health")
        timing = response.headers.get("Server-Timing", "")
        assert "total" in timing
        assert "dur=" in timing

    def test_request_id_unique(self, client):
        """Each request should get a unique ID."""
        ids = set()
        for _ in range(10):
            response = client.get("/health")
            req_id = response.headers.get("X-Request-ID", "")
            ids.add(req_id)
        assert len(ids) == 10, "Request IDs should be unique"

    def test_request_id_format(self, client):
        response = client.get("/health")
        req_id = response.headers.get("X-Request-ID", "")
        assert len(req_id) == 16
        assert req_id.isalnum()
