"""Tests for EvalForge configuration."""

from __future__ import annotations

from evalforge.config import Settings, get_settings


class TestSettings:
    """Tests for the Settings model."""

    def test_default_backend(self) -> None:
        s = Settings()
        assert s.DEFAULT_BACKEND == "mock"

    def test_openai_model_default(self) -> None:
        s = Settings()
        assert s.OPENAI_MODEL == "gpt-4"

    def test_similarity_threshold(self) -> None:
        s = Settings()
        assert s.SIMILARITY_THRESHOLD == 0.8

    def test_env_prefix(self) -> None:
        s = Settings()
        assert s.model_config.get("env_prefix") == "EVALFORGE_"


class TestGetSettings:
    """Tests for the cached get_settings function."""

    def test_cached(self) -> None:
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
