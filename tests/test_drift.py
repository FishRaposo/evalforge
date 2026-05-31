"""Tests for drift detection module."""

from __future__ import annotations

from pathlib import Path

import pytest

from evalforge.drift import DriftDetector, DriftResult
from evalforge.models.report import Report, ReportSummary
from evalforge.models.test_result import TestResult


def _make_report(
    suite_name: str = "Test Suite",
    total: int = 3,
    passed: int = 2,
    failed: int = 1,
    avg_score: float = 0.75,
    results: list[TestResult] | None = None,
) -> Report:
    if results is None:
        results = [
            TestResult(test_case_id="tc-001", test_case_name="Test 1", passed=True, score=1.0),
            TestResult(test_case_id="tc-002", test_case_name="Test 2", passed=True, score=0.8),
            TestResult(test_case_id="tc-003", test_case_name="Test 3", passed=False, score=0.3),
        ][:total]
    summary = ReportSummary(
        total=total,
        passed=passed,
        failed=failed,
        skipped=0,
        pass_rate=passed / total if total > 0 else 0.0,
        avg_score=avg_score,
    )
    return Report(
        suite_name=suite_name,
        summary=summary,
        results=results,
        metadata={},
    )


class TestDriftDetector:

    def test_pass_to_fail_detection(self) -> None:
        detector = DriftDetector(threshold=0.1)
        baseline = _make_report(
            total=2, passed=2, failed=0, avg_score=1.0,
            results=[
                TestResult(test_case_id="tc-001", test_case_name="Test 1", passed=True, score=1.0),
                TestResult(test_case_id="tc-002", test_case_name="Test 2", passed=True, score=1.0),
            ],
        )
        current = _make_report(
            total=2,
            passed=1,
            failed=1,
            avg_score=0.5,
            results=[
                TestResult(test_case_id="tc-001", test_case_name="Test 1", passed=True, score=1.0),
                TestResult(test_case_id="tc-002", test_case_name="Test 2", passed=False, score=0.0),
            ],
        )

        result = detector.compare(baseline, current)

        assert result.is_regression is True
        assert any(ct["change"] == "pass_to_fail" for ct in result.changed_tests)

    def test_fail_to_pass_detection(self) -> None:
        detector = DriftDetector(threshold=0.1)
        baseline = _make_report(
            total=2,
            passed=1,
            failed=1,
            avg_score=0.5,
            results=[
                TestResult(test_case_id="tc-001", test_case_name="Test 1", passed=True, score=1.0),
                TestResult(test_case_id="tc-002", test_case_name="Test 2", passed=False, score=0.0),
            ],
        )
        current = _make_report(
            total=2,
            passed=2,
            failed=0,
            avg_score=1.0,
            results=[
                TestResult(test_case_id="tc-001", test_case_name="Test 1", passed=True, score=1.0),
                TestResult(test_case_id="tc-002", test_case_name="Test 2", passed=True, score=1.0),
            ],
        )

        result = detector.compare(baseline, current)

        assert result.is_regression is False
        assert any(ct["change"] == "fail_to_pass" for ct in result.changed_tests)

    def test_no_change_detection(self) -> None:
        detector = DriftDetector(threshold=0.1)
        baseline = _make_report(
            total=1, passed=1, failed=0, avg_score=1.0,
            results=[
                TestResult(test_case_id="tc-001", test_case_name="Test 1", passed=True, score=1.0),
            ],
        )
        current = _make_report(
            total=1, passed=1, failed=0, avg_score=1.0,
            results=[
                TestResult(test_case_id="tc-001", test_case_name="Test 1", passed=True, score=1.0),
            ],
        )

        result = detector.compare(baseline, current)

        assert result.is_regression is False
        assert len(result.changed_tests) == 0

    def test_regression_threshold(self) -> None:
        detector = DriftDetector(threshold=0.1)
        baseline = _make_report(
            total=1, passed=1, failed=0, avg_score=0.95,
            results=[
                TestResult(test_case_id="tc-001", test_case_name="Test 1", passed=True, score=0.95),
            ],
        )
        current = _make_report(
            total=1,
            passed=1,
            failed=0,
            avg_score=0.92,
            results=[
                TestResult(test_case_id="tc-001", test_case_name="Test 1", passed=True, score=0.92),
            ],
        )

        result = detector.compare(baseline, current)

        assert result.avg_score_delta >= -0.1

    def test_report_save_load_round_trip(self, tmp_path: Path) -> None:
        report = _make_report()

        save_path = tmp_path / "drift_report.json"
        DriftDetector.save_report(report, save_path)

        assert save_path.exists()

        loaded = DriftDetector.load_report(save_path)

        assert loaded.suite_name == report.suite_name
        assert loaded.summary.total == report.summary.total
        assert loaded.summary.passed == report.summary.passed
