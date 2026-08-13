"""Edge-case tests for drift detection not covered by the baseline suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from evalforge.drift import DriftDetector
from evalforge.models.report import Report, ReportSummary
from evalforge.models.test_result import TestResult


def _report(results: list[TestResult], avg_score: float, pass_rate: float) -> Report:
    passed = sum(1 for r in results if r.passed)
    return Report(
        suite_name="Edge Suite",
        summary=ReportSummary(
            total=len(results),
            passed=passed,
            failed=len(results) - passed,
            skipped=0,
            pass_rate=pass_rate,
            avg_score=avg_score,
        ),
        results=results,
        metadata={},
    )


def test_added_and_removed_tests_are_reported() -> None:
    """Suite shape changes should be explicit in evidence, not silently ignored."""
    detector = DriftDetector(threshold=0.1)
    baseline = _report(
        [
            TestResult(test_case_id="a", test_case_name="A", passed=True, score=1.0),
            TestResult(
                test_case_id="removed",
                test_case_name="Removed",
                passed=True,
                score=1.0,
            ),
        ],
        avg_score=1.0,
        pass_rate=1.0,
    )
    current = _report(
        [
            TestResult(test_case_id="a", test_case_name="A", passed=True, score=1.0),
            TestResult(test_case_id="b", test_case_name="B", passed=False, score=0.0),
        ],
        avg_score=0.5,
        pass_rate=0.5,
    )
    result = detector.compare(baseline, current)
    assert result.added_tests == ["b"]
    assert result.removed_tests == ["removed"]


def test_score_deltas_are_reported_for_unchanged_status() -> None:
    detector = DriftDetector(threshold=0.1)
    baseline = _report(
        [TestResult(test_case_id="a", test_case_name="A", passed=True, score=0.9)],
        avg_score=0.9,
        pass_rate=1.0,
    )
    current = _report(
        [TestResult(test_case_id="a", test_case_name="A", passed=True, score=0.7)],
        avg_score=0.7,
        pass_rate=1.0,
    )

    result = detector.compare(baseline, current)

    assert result.score_deltas == [
        {
            "test_case_id": "a",
            "test_case_name": "A",
            "baseline_score": 0.9,
            "current_score": 0.7,
            "score_delta": -0.2,
        }
    ]


def test_pass_rate_regression_alone_triggers() -> None:
    detector = DriftDetector(threshold=0.1)
    baseline = _report(
        [TestResult(test_case_id="a", test_case_name="A", passed=True, score=0.9)],
        avg_score=0.9,
        pass_rate=1.0,
    )
    current = _report(
        [TestResult(test_case_id="a", test_case_name="A", passed=False, score=0.85)],
        avg_score=0.85,
        pass_rate=0.5,
    )
    result = detector.compare(baseline, current)
    assert result.is_regression is True
    assert result.pass_rate_delta == pytest.approx(-0.5)


def test_custom_threshold_suppresses_small_drops() -> None:
    detector = DriftDetector(threshold=0.5)
    baseline = _report(
        [TestResult(test_case_id="a", test_case_name="A", passed=True, score=0.9)],
        avg_score=0.9,
        pass_rate=1.0,
    )
    current = _report(
        [TestResult(test_case_id="a", test_case_name="A", passed=True, score=0.7)],
        avg_score=0.7,
        pass_rate=1.0,
    )
    result = detector.compare(baseline, current)
    # 0.2 drop is under the 0.5 threshold -> no regression.
    assert result.is_regression is False


def test_drift_result_serializes(tmp_path: Path) -> None:
    detector = DriftDetector()
    baseline = _report(
        [TestResult(test_case_id="a", test_case_name="A", passed=True, score=1.0)],
        avg_score=1.0,
        pass_rate=1.0,
    )
    current = _report(
        [TestResult(test_case_id="a", test_case_name="A", passed=True, score=1.0)],
        avg_score=1.0,
        pass_rate=1.0,
    )
    result = detector.compare(baseline, current)
    payload = result.model_dump_json()
    assert "pass_rate_delta" in payload
    assert result.suite_name == "Edge Suite"
