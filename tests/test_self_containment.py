"""Regression tests for EvalForge's vendored shared infrastructure."""

from __future__ import annotations

import builtins
import importlib
import sys
from typing import Any

import pytest


def _clear_evalforge_imports() -> None:
    """Clear modules whose imports are the subject of this regression test."""
    for module_name in list(sys.modules):
        if module_name in {"evalforge.config", "evalforge.server.app"} or (
            module_name.startswith("evalforge.shared_core")
        ):
            sys.modules.pop(module_name, None)


def _block_external_shared_core(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make an accidental import of an installed external package fail loudly."""
    real_import = builtins.__import__

    def blocked_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "shared_core" or name.startswith("shared_core."):
            raise ModuleNotFoundError(
                "external shared_core is intentionally unavailable in this test"
            )
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)


def test_config_loads_without_external_shared_core(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Configuration must resolve the vendored base class, not a sibling package."""
    _clear_evalforge_imports()
    _block_external_shared_core(monkeypatch)

    config = importlib.import_module("evalforge.config")

    assert config.Settings().DEFAULT_BACKEND == "mock"


def test_server_loads_without_external_shared_core(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The history API must resolve vendored middleware and error handling."""
    _clear_evalforge_imports()
    _block_external_shared_core(monkeypatch)

    server_app = importlib.import_module("evalforge.server.app")

    assert callable(server_app.create_app)
