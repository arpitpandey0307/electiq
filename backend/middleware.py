"""
ElectIQ — Security & Performance Middleware

Implements defense-in-depth security patterns:
- Security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
- Token-bucket rate limiting per client IP
- Structured request logging with timing for Cloud Run monitoring
"""

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config import (
    logger,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    APP_ENV,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Inject OWASP-recommended security headers into all responses.

    Protects against common web vulnerabilities including XSS,
    clickjacking, MIME sniffing, and unauthorized framing.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable browser XSS filter
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy — restrict resource origins
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://generativelanguage.googleapis.com; "
            "frame-ancestors 'none'"
        )

        # Referrer policy — limit referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy — disable unnecessary browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # HSTS for production (Cloud Run uses HTTPS)
        if APP_ENV != "development":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token-bucket rate limiter scoped per client IP address.

    Protects API endpoints from abuse while allowing static file
    and health check requests to pass through without limits.
    Rate-limited responses include a Retry-After header.
    """

    def __init__(
        self,
        app,
        max_requests: int = RATE_LIMIT_REQUESTS,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Only rate-limit API endpoints (not static files or health)
        if not path.startswith("/api/") or path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window_seconds

        # Evict expired entries
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > window_start
        ]

        if len(self._requests[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded: ip={client_ip} path={path}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please wait before trying again.",
                    "retry_after": self.window_seconds,
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Structured request logging with response timing.

    Logs are formatted as JSON for automatic parsing by Google Cloud
    Logging, enabling filtering by severity, latency, and path in
    the Google Cloud Console.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Skip logging for static assets to reduce noise
        if path.startswith(("/css/", "/js/", "/assets/")):
            return await call_next(request)

        start_time = time.time()

        try:
            response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000, 2)

            logger.info(
                f"{request.method} {path} -> {response.status_code} "
                f"({duration_ms}ms)"
            )

            # Server-Timing header for performance monitoring
            response.headers["Server-Timing"] = f"total;dur={duration_ms}"
            return response

        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"{request.method} {path} -> ERROR ({duration_ms}ms): {exc}"
            )
            raise
