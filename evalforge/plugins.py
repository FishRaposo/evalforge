"""Custom judge plugin system for user-defined evaluation logic."""

from __future__ import annotations

import importlib
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
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "judge"):
        raise AttributeError(f"Module {module_path} must define a 'judge' function")

    name = judge_name or path.stem
    return CustomJudge(getattr(module, "judge"), name=name)
