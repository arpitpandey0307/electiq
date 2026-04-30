# Security Policy

## Overview

ElectIQ implements defense-in-depth security following OWASP best practices for web application security.

## Security Measures

### Transport Layer
- **HSTS**: HTTP Strict Transport Security enforced in production (`max-age=31536000; includeSubDomains`)
- **Cloud Run**: All traffic served over HTTPS by default via Google Cloud Run's managed TLS

### HTTP Security Headers
All responses include the following headers:
| Header | Value | Purpose |
|--------|-------|---------|
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-XSS-Protection` | `1; mode=block` | Enable browser XSS filter |
| `Content-Security-Policy` | Restrictive policy | Prevent XSS, data injection |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limit referrer data |
| `Permissions-Policy` | Restrictive | Disable camera, mic, geolocation |

### Input Validation
- **Pydantic models** enforce type safety, length limits, and pattern matching on all API inputs
- **HTML entity escaping** on chat messages prevents stored/reflected XSS
- **Role validation** restricts to allowed values (`voter`, `candidate`, `journalist`, `student`)
- **Message length limits** (max 2000 chars) prevent abuse
- **History length limits** (max 20 entries) prevent excessive token usage

### Rate Limiting
- Token-bucket rate limiter: **30 requests per 60 seconds** per client IP
- Applied only to `/api/*` endpoints (static files excluded)
- Returns `429 Too Many Requests` with `Retry-After` header

### AI Safety
- **Gemini Safety Settings** configured to block medium-and-above for:
  - Harassment
  - Hate speech
  - Sexually explicit content
  - Dangerous content
- Non-partisan system prompt prevents political bias

### Container Security
- **Non-root user** in Docker container (CIS Docker Benchmark compliance)
- **Minimal base image** (`python:3.11-slim`) reduces attack surface
- **No cached pip packages** in image
- **Health check** configured for container orchestration

### Secrets Management
- API keys loaded from environment variables only
- `.env` files excluded from git via `.gitignore`
- No secrets in source code or Docker image

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly by emailing the project maintainers.
