"""
ElectIQ — Election Process Education Assistant
FastAPI Application Entrypoint

Configures the middleware stack, API routers, static file serving,
and application lifecycle events for Google Cloud Run deployment.

Google Cloud Services:
    - Google Cloud Run (deployment target)
    - Google Gemini API (AI chat backend)
    - Google Cloud Logging (structured logging)
    - Google Fonts (typography CDN)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from backend.config import (
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    ALLOWED_ORIGINS,
    FRONTEND_DIR,
    GEMINI_API_KEY,
    logger,
)
from backend.middleware import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
)
from backend.models import HealthResponse, ErrorResponse


# ── Application Lifecycle ──


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage startup and shutdown events.

    On startup: pre-load data cache and initialize Gemini client.
    On shutdown: clean up resources.
    """
    # ── Startup ──
    logger.info("Starting %s v%s", APP_NAME, APP_VERSION)

    from backend.config import DataCache
    DataCache.get_instance()

    from backend.services.gemini_service import GeminiService
    GeminiService.initialize()
    logger.info("Application startup complete")

    yield

    # ── Shutdown ──
    logger.info("Application shutdown complete")


# ── Initialize FastAPI ──

app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    responses={
        422: {"model": ErrorResponse, "description": "Validation Error"},
        429: {"model": ErrorResponse, "description": "Rate Limit Exceeded"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)


# ── Global Exception Handlers ──


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Catch-all exception handler for unhandled errors.

    Logs the error with request context and returns a standardized
    error response to prevent information leakage.
    """
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred. Please try again later.",
            "error_code": "INTERNAL_ERROR",
        },
    )


# ── Middleware Stack (applied bottom-to-top) ──

# GZip compression for responses > 256 bytes
app.add_middleware(GZipMiddleware, minimum_size=256)

# CORS — restrict origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    max_age=3600,  # Cache preflight responses for 1 hour
)

# Security headers (CSP, HSTS, COOP, CORP, X-Frame-Options, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting (30 requests/minute per IP on API routes)
app.add_middleware(RateLimitMiddleware)

# Structured request logging for Google Cloud Logging
app.add_middleware(RequestLoggingMiddleware)


# ── API Routers ──

from backend.routers import chat, timeline, quiz, scenarios  # noqa: E402

app.include_router(chat.router, tags=["Chat"])
app.include_router(timeline.router, tags=["Timeline"])
app.include_router(quiz.router, tags=["Quiz"])
app.include_router(scenarios.router, tags=["Scenarios"])


# ── Static File Serving ──

app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
app.mount(
    "/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets"
)


# ── Root & Health Endpoints ──


@app.get("/", include_in_schema=False)
async def serve_index() -> FileResponse:
    """Serve the main single-page application shell."""
    return FileResponse(
        FRONTEND_DIR / "index.html",
        media_type="text/html",
        headers={"Cache-Control": "no-cache"},
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check for Cloud Run",
    description="Returns service health status and configuration state. "
    "Used by Google Cloud Run for readiness and liveness probes.",
)
async def health_check() -> HealthResponse:
    """Health check endpoint for Google Cloud Run probes."""
    return HealthResponse(
        status="healthy",
        service=APP_NAME,
        version=APP_VERSION,
        gemini_configured=bool(GEMINI_API_KEY),
    )
