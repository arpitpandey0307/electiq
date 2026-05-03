"""
ElectIQ — Centralized Configuration Module

Manages all application settings with type-safe defaults and environment
variable overrides. Provides structured logging compatible with Google
Cloud Logging and an in-memory cache for static JSON data to eliminate
redundant disk I/O.

Google Cloud Services Used:
    - Google Cloud Logging (structured JSON log format)
    - Google Gemini API (AI chat configuration)
    - Google Cloud Run (deployment environment)
"""

from __future__ import annotations

import os
import json
import logging
import uuid
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "APP_DESCRIPTION",
    "APP_ENV",
    "DEBUG",
    "ALLOWED_ORIGINS",
    "MAX_CHAT_MESSAGE_LENGTH",
    "MAX_CHAT_HISTORY_LENGTH",
    "RATE_LIMIT_REQUESTS",
    "RATE_LIMIT_WINDOW_SECONDS",
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
    "GEMINI_TIMEOUT_SECONDS",
    "GEMINI_MAX_OUTPUT_TOKENS",
    "GEMINI_TEMPERATURE",
    "BASE_DIR",
    "DATA_DIR",
    "FRONTEND_DIR",
    "logger",
    "DataCache",
    "generate_request_id",
]

# Load environment variables from .env file (no-op if absent in Cloud Run)
load_dotenv()

# ── Application Paths ──
BASE_DIR: Path = Path(__file__).parent
DATA_DIR: Path = BASE_DIR / "data"
FRONTEND_DIR: Path = BASE_DIR.parent / "frontend"

# ── Application Settings ──
APP_NAME: str = "ElectIQ"
APP_VERSION: str = "1.0.0"
APP_DESCRIPTION: str = (
    "Election Process Education Assistant — "
    "AI-powered, gamified civic education platform"
)
APP_ENV: str = os.getenv("APP_ENV", "production")
DEBUG: bool = APP_ENV == "development"

# ── Security Settings ──
ALLOWED_ORIGINS: list[str] = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if o.strip()
] or ["*"]

MAX_CHAT_MESSAGE_LENGTH: int = 2000
MAX_CHAT_HISTORY_LENGTH: int = 20
RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_MAX_CLIENTS: int = int(os.getenv("RATE_LIMIT_MAX_CLIENTS", "10000"))

# ── Google Gemini AI Settings ──
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_TIMEOUT_SECONDS: int = 60
GEMINI_MAX_OUTPUT_TOKENS: int = 1024
GEMINI_TEMPERATURE: float = 0.7

# ── Logging ──
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()


def generate_request_id() -> str:
    """Generate a unique request ID for tracing across Google Cloud services."""
    return uuid.uuid4().hex[:16]


def configure_logging() -> logging.Logger:
    """
    Configure structured JSON logging compatible with Google Cloud Logging.

    Cloud Run automatically parses JSON-formatted stdout logs and maps
    the 'severity' field to Cloud Logging severity levels, enabling
    filtering and alerting in the Google Cloud Console.

    The log format follows the Google Cloud structured logging specification:
    https://cloud.google.com/logging/docs/structured-logging

    Returns:
        logging.Logger: Configured application logger instance.
    """
    app_logger = logging.getLogger("electiq")
    app_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    if not app_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '{"severity":"%(levelname)s","message":"%(message)s",'
            '"module":"%(module)s","function":"%(funcName)s",'
            '"timestamp":"%(asctime)s","logger":"%(name)s"}'
        )
        handler.setFormatter(formatter)
        app_logger.addHandler(handler)

    return app_logger


logger: logging.Logger = configure_logging()


# ── Data Cache (Singleton with Immutable Properties) ──


class DataCache:
    """
    Thread-safe, in-memory cache for static JSON knowledge-base files.

    Loads all JSON data once at startup to avoid repeated disk I/O
    on every API request. Data is treated as immutable and is safe
    to share across concurrent async request handlers.

    Design Pattern:
        Singleton — ensures exactly one cache instance exists.

    Usage::

        cache = DataCache.get_instance()
        timeline = cache.timeline
    """

    _instance: Optional[DataCache] = None

    def __init__(self) -> None:
        """Initialize empty cache containers."""
        self._timeline: dict[str, Any] = {}
        self._quiz: dict[str, Any] = {}
        self._scenarios: dict[str, Any] = {}
        self._glossary: dict[str, Any] = {}
        self._sources: dict[str, Any] = {}
        self._quiz_topic_summaries: list[dict[str, Any]] = []

    @classmethod
    def get_instance(cls) -> DataCache:
        """Return the singleton cache instance, initializing on first call."""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load_all()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (used in testing only)."""
        cls._instance = None

    def _load_json(self, filename: str) -> dict[str, Any]:
        """
        Safely load and parse a JSON file from the data directory.

        Args:
            filename: Name of the JSON file to load from the data directory.

        Returns:
            Parsed JSON data as a dictionary, or empty dict on error.
        """
        filepath = DATA_DIR / filename
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
            logger.info("Loaded data file: %s", filename)
            return data
        except FileNotFoundError:
            logger.error("Data file not found: %s", filepath)
            return {}
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON in %s: %s", filename, exc)
            return {}

    def _load_all(self) -> None:
        """Pre-load all data files into memory at startup."""
        logger.info("Initializing data cache...")
        self._timeline = self._load_json("timeline.json")
        self._quiz = self._load_json("quiz.json")
        self._scenarios = self._load_json("scenarios.json")
        self._glossary = self._load_json("glossary.json")
        self._sources = self._load_json("sources.json")
        self._precompute_quiz_summaries()
        logger.info("Data cache initialized successfully")

    def _precompute_quiz_summaries(self) -> None:
        """Pre-compute quiz topic summaries to avoid per-request computation."""
        self._quiz_topic_summaries = [
            {
                "id": key,
                "title": value.get("title", key),
                "icon": value.get("icon", "📝"),
                "question_count": len(value.get("questions", [])),
            }
            for key, value in self._quiz.items()
        ]

    @property
    def timeline(self) -> dict[str, Any]:
        """Election timeline milestones data."""
        return self._timeline

    @property
    def quiz(self) -> dict[str, Any]:
        """Quiz questions grouped by topic."""
        return self._quiz

    @property
    def quiz_topic_summaries(self) -> list[dict[str, Any]]:
        """Pre-computed quiz topic summaries for the topic selector."""
        return self._quiz_topic_summaries

    @property
    def scenarios(self) -> dict[str, Any]:
        """What-if scenario decision trees."""
        return self._scenarios

    @property
    def glossary(self) -> dict[str, Any]:
        """Election glossary terms."""
        return self._glossary

    @property
    def sources(self) -> dict[str, Any]:
        """Official source citations."""
        return self._sources
