"""
ElectIQ — Election Process Education Assistant
FastAPI Application Entrypoint

Configures middleware stack, API routers, static file serving,
and application lifecycle events for Google Cloud Run deployment.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
    DataCache,
)
from backend.middleware import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
)
from backend.models import HealthResponse


# ── Application Lifecycle ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage startup and shutdown events.

    On startup: pre-load data cache and initialize the shared
    httpx client for Gemini API calls.
    On shutdown: close the httpx client to release connections.
    """
    # Startup
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    DataCache.get_instance()

    from backend.services.gemini_service import startup_client
    await startup_client()
    logger.info("Application startup complete")

    yield

    # Shutdown
    from backend.services.gemini_service import shutdown_client
    await shutdown_client()
    logger.info("Application shutdown complete")


# ── Initialize FastAPI ──
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)


# ── Middleware Stack (applied bottom-to-top) ──

# GZip compression for responses > 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)

# CORS — restrict origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Security headers (CSP, HSTS, X-Frame-Options, etc.)
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
async def serve_index():
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
    "Used by Cloud Run for readiness and liveness probes.",
)
async def health_check() -> HealthResponse:
    """Health check endpoint for Cloud Run probes."""
    return HealthResponse(
        status="healthy",
        service=APP_NAME,
        version=APP_VERSION,
        gemini_configured=bool(GEMINI_API_KEY),
    )
