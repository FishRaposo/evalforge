"""Custom judge plugin system for user-defined evaluation logic."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from evalforge.judges.base import BaseJudge, JudgeResult
from evalforge.models.test_case import TestCase


class CustomJudge(BaseJudge):
    def __init__(self, judge_func: Any, name: str = "custom") -> None:
        self._judge_func = judge_func
        self._name = name

    def judge(self, test_case: TestCase, response: str) -> JudgeResult:
        try:
            result = self._judge_func(test_case, response)
            if isinstance(result, JudgeResult):
                return result
            if isinstance(result, bool):
                return JudgeResult(
                    passed=result, score=1.0 if result else 0.0, details={}
                )
            if isinstance(result, dict):
                return JudgeResult(**result)
            return JudgeResult(
                passed=False,
                score=0.0,
                details={"error": f"Unexpected return type: {type(result)}"},
            )
        except Exception as e:
            return JudgeResult(passed=False, score=0.0, details={"error": str(e)})


def load_judge_from_module(
    module_path: str, judge_name: str | None = None
) -> CustomJudge:
    path = Path(module_path)
    if not path.exists():
        raise FileNotFoundError(f"Judge module not found: {module_path}")

    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None:
        raise ImportError(f"Could not create module spec for {module_path}")
    if spec.loader is None:
        raise ImportError(f"Module spec has no loader for {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "judge"):
        raise AttributeError(f"Module {module_path} must define a 'judge' function")

    name = judge_name or path.stem
    return CustomJudge(getattr(module, "judge"), name=name)


def discover_plugins(directory: str) -> list[tuple[str, CustomJudge]]:
    """Discover and load all valid judge plugins in a directory.

    Args:
        directory: Path to a directory containing Python judge modules.

    Returns:
        List of (name, CustomJudge) tuples for valid plugins.
    """
    plugins: list[tuple[str, CustomJudge]] = []
    for path in Path(directory).glob("*.py"):
        try:
            judge = load_judge_from_module(str(path))
            plugins.append((judge._name, judge))
        except Exception:
            # Skip invalid plugins
            continue
    return plugins


def validate_plugin(module_path: str) -> list[str]:
    """Validate a judge module without loading it.

    Args:
        module_path: Path to the Python module.

    Returns:
        List of validation error messages (empty if valid).
    """
    errors: list[str] = []
    path = Path(module_path)
    if not path.exists():
        errors.append(f"File not found: {module_path}")
        return errors
    if not path.suffix == ".py":
        errors.append(f"Not a Python file: {module_path}")
        return errors

    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        errors.append(f"Cannot load module spec: {module_path}")
        return errors

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        errors.append(f"Import error: {exc}")
        return errors

    if not hasattr(module, "judge"):
        errors.append("Module must define a 'judge(test_case, response)' function")
    else:
        func = getattr(module, "judge")
        import inspect
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        if len(params) < 2:
            errors.append("'judge' function must accept at least 2 arguments")

    return errors
