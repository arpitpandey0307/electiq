"""
Config Module Tests for ElectIQ.

Tests DataCache singleton, data loading, logging configuration,
and utility functions.
"""

import pytest

from backend.config import (
    DataCache,
    configure_logging,
    generate_request_id,
    APP_NAME,
    APP_VERSION,
    BASE_DIR,
    DATA_DIR,
    FRONTEND_DIR,
    GEMINI_MODEL,
    GEMINI_TEMPERATURE,
    MAX_CHAT_MESSAGE_LENGTH,
    MAX_CHAT_HISTORY_LENGTH,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
)


class TestDataCacheSingleton:
    """DataCache singleton pattern tests."""

    def test_singleton_returns_same_instance(self):
        a = DataCache.get_instance()
        b = DataCache.get_instance()
        assert a is b

    def test_timeline_not_empty(self, cache):
        assert cache.timeline is not None
        assert len(cache.timeline) > 0

    def test_quiz_not_empty(self, cache):
        assert cache.quiz is not None
        assert len(cache.quiz) > 0

    def test_scenarios_not_empty(self, cache):
        assert cache.scenarios is not None
        assert len(cache.scenarios) > 0

    def test_glossary_not_empty(self, cache):
        assert cache.glossary is not None
        assert len(cache.glossary) > 0

    def test_sources_not_empty(self, cache):
        assert cache.sources is not None
        assert len(cache.sources) > 0

    def test_quiz_topic_summaries_precomputed(self, cache):
        summaries = cache.quiz_topic_summaries
        assert len(summaries) > 0
        assert all("id" in s for s in summaries)
        assert all("title" in s for s in summaries)
        assert all("question_count" in s for s in summaries)

    def test_quiz_summaries_match_quiz_data(self, cache):
        assert len(cache.quiz_topic_summaries) == len(cache.quiz)


class TestConfigureLogging:
    """Logging configuration tests."""

    def test_logger_returns_logger(self):
        lg = configure_logging()
        assert lg is not None
        assert lg.name == "electiq"

    def test_logger_has_handlers(self):
        lg = configure_logging()
        assert len(lg.handlers) > 0


class TestGenerateRequestId:
    """Request ID generation tests."""

    def test_returns_string(self):
        rid = generate_request_id()
        assert isinstance(rid, str)

    def test_correct_length(self):
        rid = generate_request_id()
        assert len(rid) == 16

    def test_unique(self):
        ids = {generate_request_id() for _ in range(100)}
        assert len(ids) == 100

    def test_alphanumeric(self):
        rid = generate_request_id()
        assert rid.isalnum()


class TestConfigConstants:
    """Test configuration constants are valid."""

    def test_app_name(self):
        assert APP_NAME == "ElectIQ"

    def test_app_version_semver(self):
        parts = APP_VERSION.split(".")
        assert len(parts) == 3

    def test_base_dir_exists(self):
        assert BASE_DIR.exists()

    def test_data_dir_exists(self):
        assert DATA_DIR.exists()

    def test_frontend_dir_exists(self):
        assert FRONTEND_DIR.exists()

    def test_gemini_model_set(self):
        assert len(GEMINI_MODEL) > 0

    def test_gemini_temperature_range(self):
        assert 0.0 <= GEMINI_TEMPERATURE <= 2.0

    def test_chat_limits_positive(self):
        assert MAX_CHAT_MESSAGE_LENGTH > 0
        assert MAX_CHAT_HISTORY_LENGTH > 0

    def test_rate_limit_positive(self):
        assert RATE_LIMIT_REQUESTS > 0
        assert RATE_LIMIT_WINDOW_SECONDS > 0
