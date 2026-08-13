"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import SettingsConfigDict

from evalforge.shared_core.config import BaseAppConfig


class Settings(BaseAppConfig):
    """EvalForge application settings.

    Extends the vendored ``evalforge.shared_core.config.BaseAppConfig`` (inheriting
    DATABASE_URL, REDIS_URL, LOG_LEVEL, ...) while keeping EvalForge's
    ``EVALFORGE_`` env prefix and domain knobs. ``OPENAI_API_KEY`` is overridden to a
    plain ``str`` (the base declares it as ``Optional[SecretStr]``) to preserve
    EvalForge's backend call sites.
    """

    DEFAULT_BACKEND: str = "mock"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4"
    SIMILARITY_THRESHOLD: float = 0.8
    REQUEST_TIMEOUT: int = 30
    MAX_CONCURRENT_REQUESTS: int = 5
    REPORT_OUTPUT_DIR: str = "./reports"

    model_config = SettingsConfigDict(
        env_prefix="EVALFORGE_", env_file=".env", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Returns:
        The application settings loaded from environment variables.
    """
    return Settings()
