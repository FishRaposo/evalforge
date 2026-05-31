"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """EvalForge application settings.

    Attributes:
        DEFAULT_BACKEND: Default backend to use for evaluations.
        OPENAI_API_KEY: API key for OpenAI-compatible backends.
        OPENAI_BASE_URL: Base URL for the OpenAI-compatible API.
        OPENAI_MODEL: Model identifier to use for API calls.
        SIMILARITY_THRESHOLD: Default threshold for semantic similarity judges.
        REQUEST_TIMEOUT: Maximum seconds to wait for a backend response.
        MAX_CONCURRENT_REQUESTS: Maximum number of parallel requests to the backend.
        REPORT_OUTPUT_DIR: Default directory for generated reports.
    """

    DEFAULT_BACKEND: str = "mock"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4"
    SIMILARITY_THRESHOLD: float = 0.8
    REQUEST_TIMEOUT: int = 30
    MAX_CONCURRENT_REQUESTS: int = 5
    REPORT_OUTPUT_DIR: str = "./reports"

    model_config = {"env_prefix": "EVALFORGE_", "env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Returns:
        The application settings loaded from environment variables.
    """
    return Settings()
