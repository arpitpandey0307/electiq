# Security Policy

## Overview

ElectIQ implements defense-in-depth security following OWASP best practices for web application security. All security measures are tested in the automated test suite.

## Security Measures

### Transport Layer
- **HSTS**: HTTP Strict Transport Security enforced in production (`max-age=31536000; includeSubDomains; preload`)
- **Cloud Run**: All traffic served over HTTPS by default via Google Cloud Run's managed TLS

### HTTP Security Headers
All responses include the following headers (verified by automated tests):
| Header | Value | Purpose |
|--------|-------|---------|
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-XSS-Protection` | `1; mode=block` | Enable browser XSS filter |
| `Content-Security-Policy` | Restrictive policy | Prevent XSS, data injection |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limit referrer data |
| `Permissions-Policy` | Restrictive | Disable camera, mic, geolocation |
| `Cross-Origin-Opener-Policy` | `same-origin` | Cross-origin isolation |
| `Cross-Origin-Resource-Policy` | `same-origin` | Resource restriction |
| `X-Permitted-Cross-Domain-Policies` | `none` | Block Flash/PDF |
| `Strict-Transport-Security` | Production only | HTTPS enforcement with preload |

### Input Validation
- **Pydantic models** enforce type safety, length limits, and pattern matching on all API inputs
- **HTML entity escaping** on chat messages prevents stored/reflected XSS
- **Role validation** restricts to allowed values (`voter`, `candidate`, `journalist`, `student`)
- **Message length limits** (max 2000 chars) prevent abuse
- **History length limits** (max 20 entries) prevent excessive token usage
- **History entry validation** ensures each entry has required `role` and `content` keys
- **Query parameter validation** via `SuggestionQueryParams` model

### Rate Limiting
- Token-bucket rate limiter: **30 requests per 60 seconds** per client IP
- Applied only to `/api/*` endpoints (static files and health excluded)
- **LRU eviction** caps tracked clients at 10,000 (prevents memory DoS)
- Returns `429 Too Many Requests` with `Retry-After` header
- Structured logging of rate-limit violations

### AI Safety
- **Google Gemini Safety Settings** via official SDK configured to block medium-and-above for:
  - Harassment (`HARM_CATEGORY_HARASSMENT`)
  - Hate speech (`HARM_CATEGORY_HATE_SPEECH`)
  - Sexually explicit content (`HARM_CATEGORY_SEXUALLY_EXPLICIT`)
  - Dangerous content (`HARM_CATEGORY_DANGEROUS_CONTENT`)
- Non-partisan system prompt prevents political bias
- Graceful fallback to curated responses on API errors

### Container Security
- **Non-root user** in Docker container (CIS Docker Benchmark compliance)
- **Minimal base image** (`python:3.11-slim`) reduces attack surface
- **No cached pip packages** in image
- **Health check** configured for container orchestration

### Observability & Tracing
- **X-Request-ID** header on every response for distributed tracing
- **Server-Timing** header for performance monitoring
- **Structured JSON logging** compatible with Google Cloud Logging

### Secrets Management
- API keys loaded from environment variables only
- `.env` files excluded from git via `.gitignore`
- No secrets in source code or Docker image

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly by emailing the project maintainers.
