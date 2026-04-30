# ──────────────────────────────────────────────
# ElectIQ — Optimized Production Dockerfile
#
# Security: Non-root user, minimal attack surface
# Efficiency: Layer caching, slim base, .dockerignore
# Cloud Run: PORT env variable, health check support
# ──────────────────────────────────────────────

FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first for Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Create non-root user for security (CIS Docker Benchmark)
RUN groupadd -r electiq && \
    useradd -r -g electiq -d /app -s /sbin/nologin electiq && \
    chown -R electiq:electiq /app

USER electiq

# Expose the Cloud Run default port
EXPOSE 8080

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Cloud Run injects PORT env variable; default to 8080
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
