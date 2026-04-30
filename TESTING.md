# Testing Guide

## Overview

ElectIQ uses **pytest** for comprehensive testing across API endpoints, security, data integrity, and model validation.

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
```

## Test Structure

```
tests/
├── __init__.py              # Test package marker
├── conftest.py              # Shared fixtures (TestClient, sample data)
├── test_api_endpoints.py    # All API route tests (happy + error paths)
├── test_security.py         # Security headers, input validation, data integrity
└── test_models.py           # Pydantic model constraint tests
```

## Test Categories

### API Endpoint Tests (`test_api_endpoints.py`)
- **Health Check**: Status 200, response schema, config detection
- **Timeline**: Milestone data structure, valid statuses, required fields
- **Quiz**: Topic listing, per-topic retrieval, question structure, 404 handling
- **Scenarios**: Scenario list, decision tree structure, unique IDs
- **Glossary**: Term list, required fields, non-empty content
- **Chat**: Suggestions per role, SSE streaming, input validation (422 errors)
- **Index Page**: HTML serving, content type, app name presence

### Security Tests (`test_security.py`)
- **Security Headers**: X-Frame-Options, CSP, XSS-Protection, HSTS, Permissions-Policy
- **Input Validation**: Oversized messages (422), invalid roles (422), HTML sanitization
- **Data Integrity**: Quiz answer ranges, explanation quality, date validity, uniqueness
- **Performance**: Response time benchmarks, Server-Timing header presence

### Model Tests (`test_models.py`)
- **ChatRequest**: Role validation, message length, HTML escaping, defaults
- **HealthResponse**: Schema compliance, serialization roundtrip
- **QuizTopicSummary**: Field presence, serialization

## Coverage Target

Minimum coverage threshold: **70%** (configured in `pyproject.toml`).

```bash
# Generate HTML coverage report
pytest --cov=backend --cov-report=html
open htmlcov/index.html
```
