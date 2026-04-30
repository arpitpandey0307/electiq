"""
ElectIQ — Centralized Configuration Module

Manages all application settings with type-safe defaults and environment
variable overrides. Provides structured logging for Google Cloud Run
and an in-memory cache for static JSON data to eliminate redundant disk I/O.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file (no-op if absent in Cloud Run)
load_dotenv()

# ── Application Paths ──
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# ── Application Settings ──
APP_NAME = "ElectIQ"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = (
    "Election Process Education Assistant — "
    "AI-powered, gamified civic education"
)
APP_ENV = os.getenv("APP_ENV", "production")
DEBUG = APP_ENV == "development"

# ── Security Settings ──
ALLOWED_ORIGINS: list[str] = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()
]
MAX_CHAT_MESSAGE_LENGTH = 2000
MAX_CHAT_HISTORY_LENGTH = 20
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# ── Gemini AI Settings ──
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_STREAM_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:streamGenerateContent"
)
GEMINI_TIMEOUT_SECONDS = 60
GEMINI_MAX_OUTPUT_TOKENS = 1024
GEMINI_TEMPERATURE = 0.7

# ── Logging ──
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def configure_logging() -> logging.Logger:
    """
    Configure structured JSON logging compatible with Google Cloud Logging.

    Cloud Run automatically parses JSON-formatted stdout logs and maps
    the 'severity' field to Cloud Logging severity levels, enabling
    filtering and alerting in the Google Cloud Console.
    """
    app_logger = logging.getLogger("electiq")
    app_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    if not app_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '{"severity":"%(levelname)s","message":"%(message)s",'
            '"module":"%(module)s","function":"%(funcName)s",'
            '"timestamp":"%(asctime)s"}'
        )
        handler.setFormatter(formatter)
        app_logger.addHandler(handler)

    return app_logger


logger = configure_logging()


# ── Data Cache (Singleton) ──
class DataCache:
    """
    In-memory cache for static JSON knowledge-base files.

    Loads all JSON data once at startup to avoid repeated disk I/O
    on every API request. Data is immutable and safe to share across
    concurrent async request handlers.

    Usage:
        cache = DataCache.get_instance()
        timeline = cache.timeline
    """

    _instance: Optional["DataCache"] = None

    def __init__(self) -> None:
        self._timeline: dict = {}
        self._quiz: dict = {}
        self._scenarios: dict = {}
        self._glossary: dict = {}
        self._sources: dict = {}

    @classmethod
    def get_instance(cls) -> "DataCache":
        """Return the singleton cache instance, initializing on first call."""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load_all()
        return cls._instance

    def _load_json(self, filename: str) -> dict:
        """Safely load and parse a JSON file from the data directory."""
        filepath = DATA_DIR / filename
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded data file: {filename}")
            return data
        except FileNotFoundError:
            logger.error(f"Data file not found: {filepath}")
            return {}
        except json.JSONDecodeError as exc:
            logger.error(f"Invalid JSON in {filename}: {exc}")
            return {}

    def _load_all(self) -> None:
        """Pre-load all data files into memory at startup."""
        logger.info("Initializing data cache...")
        self._timeline = self._load_json("timeline.json")
        self._quiz = self._load_json("quiz.json")
        self._scenarios = self._load_json("scenarios.json")
        self._glossary = self._load_json("glossary.json")
        self._sources = self._load_json("sources.json")
        logger.info("Data cache initialized successfully")

    @property
    def timeline(self) -> dict:
        """Election timeline milestones data."""
        return self._timeline

    @property
    def quiz(self) -> dict:
        """Quiz questions grouped by topic."""
        return self._quiz

    @property
    def scenarios(self) -> dict:
        """What-if scenario decision trees."""
        return self._scenarios

    @property
    def glossary(self) -> dict:
        """Election glossary terms."""
        return self._glossary

    @property
    def sources(self) -> dict:
        """Official source citations."""
        return self._sources
