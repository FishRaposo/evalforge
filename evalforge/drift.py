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
    added_tests: list[str] = Field(default_factory=list)
    removed_tests: list[str] = Field(default_factory=list)
    score_deltas: list[dict[str, Any]] = Field(default_factory=list)


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
        baseline_ids = {result.test_case_id for result in baseline.results}
        current_ids = {result.test_case_id for result in current.results}

        return DriftResult(
            suite_name=current.suite_name,
            baseline_timestamp=baseline.timestamp.isoformat(),
            current_timestamp=current.timestamp.isoformat(),
            pass_rate_delta=pass_rate_delta,
            avg_score_delta=avg_score_delta,
            is_regression=is_regression,
            changed_tests=changed_tests,
            added_tests=sorted(current_ids - baseline_ids),
            removed_tests=sorted(baseline_ids - current_ids),
            score_deltas=self._find_score_deltas(baseline, current),
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
                        "score_delta": round(
                            current_result.score - baseline_result.score, 6
                        ),
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
                        "score_delta": round(
                            current_result.score - baseline_result.score, 6
                        ),
                    }
                )

        return sorted(changed, key=lambda item: item["test_case_id"])

    def _find_score_deltas(
        self, baseline: Report, current: Report
    ) -> list[dict[str, Any]]:
        """Return deterministic score deltas for test IDs in both reports."""
        baseline_by_id = {result.test_case_id: result for result in baseline.results}
        current_by_id = {result.test_case_id: result for result in current.results}
        deltas: list[dict[str, Any]] = []
        for test_id in sorted(baseline_by_id.keys() & current_by_id.keys()):
            baseline_result = baseline_by_id[test_id]
            current_result = current_by_id[test_id]
            score_delta = round(current_result.score - baseline_result.score, 6)
            if score_delta == 0:
                continue
            deltas.append(
                {
                    "test_case_id": test_id,
                    "test_case_name": current_result.test_case_name,
                    "baseline_score": baseline_result.score,
                    "current_score": current_result.score,
                    "score_delta": score_delta,
                }
            )
        return deltas

    @staticmethod
    def load_report(path: Path) -> Report:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Report.model_validate(data)

    @staticmethod
    def save_report(report: Report, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return path
