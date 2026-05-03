# Testing Guide

## Overview

ElectIQ uses **pytest** for comprehensive testing with **181 tests** across **7 test files** covering API endpoints, security, models, services, middleware, configuration, and data integrity.

## Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=backend --cov-report=term-missing

# Run specific test file
pytest tests/test_api_endpoints.py

# Run specific test class
pytest tests/test_security.py::TestSecurityHeaders

# Run tests matching a keyword
pytest -k "quiz"

# Run async tests only
pytest tests/test_gemini_service.py -v
```

## Test Structure

```
tests/
├── __init__.py                  # Test package marker
├── conftest.py                  # Shared fixtures (TestClient, DataCache, sample data)
├── test_api_endpoints.py        # All API route tests (51 tests)
├── test_security.py             # Security headers, validation, data integrity (30 tests)
├── test_models.py               # Pydantic model constraint tests (22 tests)
├── test_gemini_service.py       # Gemini service + fallback tests (12 tests)
├── test_prompt_builder.py       # System prompt construction tests (16 tests)
├── test_middleware.py           # Rate limiting + logging tests (14 tests)
└── test_config.py               # DataCache + configuration tests (18 tests)
```

## Test Categories

### API Endpoint Tests (`test_api_endpoints.py`) — 51 tests
- **Health Check**: Status 200, response schema, config detection, semver version
- **Index Page**: HTML serving, lang attribute, meta description, skip link, ARIA live region
- **Timeline**: Milestone structure, valid statuses, cache headers, key facts
- **Quiz**: Topic listing, per-topic retrieval, question structure, 404 handling, cache headers
- **Scenarios**: Scenario list, decision tree structure, unique IDs, cache headers
- **Glossary**: Term list, required fields, non-empty content, cache headers
- **Chat**: Suggestions per role, SSE streaming, tokens, done signal, input validation (422 errors)

### Security Tests (`test_security.py`) — 30 tests
- **Security Headers**: X-Frame-Options, CSP, XSS-Protection, HSTS, COOP, CORP, Permissions-Policy, X-Permitted-Cross-Domain-Policies, Referrer-Policy (12 headers tested)
- **Input Validation**: Oversized messages, invalid roles, HTML sanitization, empty/whitespace messages, Unicode, special characters, invalid history entries, case insensitivity
- **Data Integrity**: Quiz answer ranges, explanation quality, date validity, uniqueness
- **Performance**: Response time benchmarks, Server-Timing header presence
- **CORS**: Origin header handling

### Model Tests (`test_models.py`) — 22 tests
- **ChatRequest**: Role validation, message sanitization, length limits, history validation, Unicode support
- **SuggestionQueryParams**: Role normalization, invalid role defaults
- **HealthResponse**: Schema compliance, serialization roundtrip
- **QuizTopicSummary**: Field presence, count validation
- **ErrorResponse**: Default and custom error codes

### Gemini Service Tests (`test_gemini_service.py`) — 12 tests
- **Initialization**: Idempotent init, availability check
- **Fallback Responses**: Content quality, source citations, keyword matching (vote, register, candidate, EVM)
- **Streaming**: Token production, topic-specific responses, history handling

### Prompt Builder Tests (`test_prompt_builder.py`) — 16 tests
- **System Prompts**: Base prompt inclusion, role-specific context, case insensitivity, invalid role defaults
- **Suggested Questions**: Per-role retrieval, meaningful content, all roles covered
- **Constants**: Prompt completeness, role coverage

### Middleware Tests (`test_middleware.py`) — 14 tests
- **Rate Limiting**: API pass-through, health bypass, static bypass, LRU eviction, window cleanup
- **Security Headers**: Headers on API, health, and root endpoints, CSP frame-ancestors
- **Request Logging**: Server-Timing header, unique request IDs, ID format

### Configuration Tests (`test_config.py`) — 18 tests
- **DataCache**: Singleton pattern, data loading (timeline, quiz, scenarios, glossary, sources), pre-computed summaries
- **Logging**: Logger creation, handler configuration
- **Request IDs**: Format, uniqueness, length
- **Constants**: Valid paths, positive limits, version format

## Coverage Target

Minimum coverage threshold: **85%** (configured in `pyproject.toml`).

```bash
# Generate HTML coverage report
pytest --cov=backend --cov-report=html
open htmlcov/index.html
```
