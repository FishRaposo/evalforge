"""Structured logging for EvalForge.

Log level is controlled via the ``EVALFORGE_LOG_LEVEL`` environment variable.
In non-development environments JSON formatting is used; otherwise plain text.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any


def _is_dev() -> bool:
    return os.getenv("EVALFORGE_ENV", "development").lower() == "development"


class _JSONFormatter(logging.Formatter):
    """JSON formatter for structured production logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def configure_logging(level: str | None = None) -> None:
    """Configure EvalForge logging.

    Args:
        level: Override log level (DEBUG, INFO, WARNING, ERROR).
               Defaults to ``EVALFORGE_LOG_LEVEL`` or INFO.
    """
    env_level = (level or os.getenv("EVALFORGE_LOG_LEVEL") or "INFO").upper()
    numeric_level = getattr(logging, env_level, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    if _is_dev():
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            )
        )
    else:
        handler.setFormatter(_JSONFormatter())

    logging.basicConfig(level=numeric_level, handlers=[handler], force=True)
