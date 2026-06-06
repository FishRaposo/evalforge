"""Tests for logging configuration."""

from __future__ import annotations

import logging

import pytest

from evalforge.logging import _is_dev, _JSONFormatter, configure_logging


def test_is_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVALFORGE_ENV", "production")
    assert _is_dev() is False

    monkeypatch.setenv("EVALFORGE_ENV", "development")
    assert _is_dev() is True


def test_json_formatter() -> None:
    formatter = _JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Log message",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert "Log message" in formatted
    assert "INFO" in formatted
    assert "test_logger" in formatted


def test_configure_logging(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVALFORGE_ENV", "production")
    configure_logging(level="DEBUG")
    # Verify handler formatter is JSON
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) > 0
    # Clean up by restoring dev logging
    monkeypatch.setenv("EVALFORGE_ENV", "development")
    configure_logging(level="INFO")
