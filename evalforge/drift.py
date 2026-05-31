"""Drift detection for comparing evaluation results over time."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from evalforge.models.report import Report


class DriftResult(BaseModel):
    suite_name: str
    baseline_timestamp: str
    current_timestamp: str
    pass_rate_delta: float
    avg_score_delta: float
    is_regression: bool
    changed_tests: list[dict[str, Any]] = Field(default_factory=list)


class DriftDetector:
    def __init__(self, threshold: float = 0.1) -> None:
        self._threshold = threshold

    def compare(self, baseline: Report, current: Report) -> DriftResult:
        pass_rate_delta = current.summary.pass_rate - baseline.summary.pass_rate
        avg_score_delta = current.summary.avg_score - baseline.summary.avg_score

        is_regression = (
            pass_rate_delta < -self._threshold or avg_score_delta < -self._threshold
        )

        changed_tests = self._find_changed_tests(baseline, current)

        return DriftResult(
            suite_name=current.suite_name,
            baseline_timestamp=baseline.timestamp.isoformat(),
            current_timestamp=current.timestamp.isoformat(),
            pass_rate_delta=pass_rate_delta,
            avg_score_delta=avg_score_delta,
            is_regression=is_regression,
            changed_tests=changed_tests,
        )

    def _find_changed_tests(
        self, baseline: Report, current: Report
    ) -> list[dict[str, Any]]:
        baseline_by_id = {r.test_case_id: r for r in baseline.results}
        current_by_id = {r.test_case_id: r for r in current.results}

        changed: list[dict[str, Any]] = []
        for test_id, current_result in current_by_id.items():
            if test_id not in baseline_by_id:
                continue
            baseline_result = baseline_by_id[test_id]
            if baseline_result.passed and not current_result.passed:
                changed.append(
                    {
                        "test_case_id": test_id,
                        "test_case_name": current_result.test_case_name,
                        "change": "pass_to_fail",
                        "baseline_score": baseline_result.score,
                        "current_score": current_result.score,
                        "score_delta": current_result.score - baseline_result.score,
                    }
                )
            elif not baseline_result.passed and current_result.passed:
                changed.append(
                    {
                        "test_case_id": test_id,
                        "test_case_name": current_result.test_case_name,
                        "change": "fail_to_pass",
                        "baseline_score": baseline_result.score,
                        "current_score": current_result.score,
                        "score_delta": current_result.score - baseline_result.score,
                    }
                )

        return changed

    @staticmethod
    def load_report(path: Path) -> Report:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Report.model_validate(data)

    @staticmethod
    def save_report(report: Report, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return path
