"""Compatibility engines over the existing judge and drift registries."""

from __future__ import annotations

from typing import Any

from evalforge.drift import DriftDetector
from evalforge.judges.base import BaseJudge, JudgeResult
from evalforge.judges.registry import get_judge
from evalforge.models.report import Report
from evalforge.models.test_case import TestCase, TestCaseType


class RegistryJudgeEngine:
    """Judge engine that preserves the public registry semantics."""

    def __init__(self, overrides: dict[TestCaseType, BaseJudge] | None = None) -> None:
        self._overrides = overrides or {}

    def evaluate(self, test_case: TestCase, response: str) -> JudgeResult:
        judge = self._overrides.get(test_case.type) or get_judge(test_case.type)
        return judge.judge(test_case, response)

    def judge(self, test_case: TestCase, response: str) -> JudgeResult:
        """Compatibility alias for callers that use judge terminology."""

        return self.evaluate(test_case, response)


class RegistryDriftEngine:
    """Drift engine backed by the existing deterministic detector."""

    def __init__(self, threshold: float = 0.1) -> None:
        self._detector = DriftDetector(threshold=threshold)

    def compare(self, baseline: Report, current: Report) -> Any:
        return self._detector.compare(baseline, current)

    @property
    def detector(self) -> DriftDetector:
        return self._detector
