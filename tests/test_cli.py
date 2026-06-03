"""Tests for EvalForge CLI commands."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from evalforge.cli import app

runner = CliRunner()


class TestEvalCommand:
    """Tests for the ``eval`` CLI command."""

    def test_eval_with_mock_backend(self, tmp_path: Path) -> None:
        suite_path = tmp_path / "suite.yaml"
        suite_path.write_text(
            "name: Test\nversion: '1.0'\ntest_cases:\n"
            "  - id: t1\n    name: Pass\n    type: exact_answer\n"
            "    input: What is 2+2?\n    expected: '4'\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["eval", str(suite_path), "--backend", "mock"])
        assert result.exit_code == 0
        assert "EvalForge" in result.output
        assert "Test" in result.output

    def test_eval_with_fail_threshold(self, tmp_path: Path) -> None:
        suite_path = tmp_path / "suite.yaml"
        suite_path.write_text(
            "name: Test\nversion: '1.0'\ntest_cases:\n"
            "  - id: t1\n    name: Pass\n    type: exact_answer\n"
            "    input: What is 2+2?\n    expected: '4'\n",
            encoding="utf-8",
        )
        result = runner.invoke(
            app, ["eval", str(suite_path), "--backend", "mock", "--fail-threshold", "0.99"]
        )
        # Mock backend default response won't match '4', so pass rate < 0.99
        assert result.exit_code == 1

    def test_eval_invalid_suite(self, tmp_path: Path) -> None:
        suite_path = tmp_path / "suite.yaml"
        suite_path.write_text("not: valid\n", encoding="utf-8")
        result = runner.invoke(app, ["eval", str(suite_path), "--backend", "mock"])
        assert result.exit_code == 1

    def test_eval_missing_file(self) -> None:
        result = runner.invoke(app, ["eval", "/nonexistent/suite.yaml"])
        assert result.exit_code == 2  # Typer validation error


class TestListSuitesCommand:
    """Tests for the ``list-suites`` CLI command."""

    def test_list_suites(self, tmp_path: Path) -> None:
        (tmp_path / "suite1.yaml").write_text(
            "name: Suite1\nversion: '1.0'\ntest_cases: []\n", encoding="utf-8"
        )
        result = runner.invoke(app, ["list-suites", "--dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "Suite1" in result.output


class TestInitCommand:
    """Tests for the ``init`` CLI command."""

    def test_init_creates_suite(self, tmp_path: Path) -> None:
        out = tmp_path / "suites"
        result = runner.invoke(app, ["init", "--output", str(out)])
        assert result.exit_code == 0
        assert (out / "sample_suite.yaml").exists()


class TestDriftCommand:
    """Tests for the ``drift`` CLI command."""

    def test_drift_detects_regression(self, tmp_path: Path) -> None:
        import json
        baseline = tmp_path / "baseline.json"
        current = tmp_path / "current.json"
        report = {
            "suite_name": "S",
            "timestamp": "2024-01-01T00:00:00",
            "summary": {"total": 2, "passed": 2, "failed": 0, "skipped": 0, "pass_rate": 1.0, "avg_score": 0.9},
            "results": [
                {"test_case_id": "t1", "test_case_name": "A", "passed": True, "score": 0.9},
                {"test_case_id": "t2", "test_case_name": "B", "passed": True, "score": 0.9},
            ],
        }
        baseline.write_text(json.dumps(report), encoding="utf-8")
        current_report = {
            "suite_name": "S",
            "timestamp": "2024-01-02T00:00:00",
            "summary": {"total": 2, "passed": 1, "failed": 1, "skipped": 0, "pass_rate": 0.5, "avg_score": 0.5},
            "results": [
                {"test_case_id": "t1", "test_case_name": "A", "passed": False, "score": 0.3},
                {"test_case_id": "t2", "test_case_name": "B", "passed": True, "score": 0.7},
            ],
        }
        current.write_text(json.dumps(current_report), encoding="utf-8")
        result = runner.invoke(app, ["drift", str(baseline), str(current)])
        assert result.exit_code == 1
        assert "Regression detected" in result.output

    def test_drift_no_regression(self, tmp_path: Path) -> None:
        import json
        baseline = tmp_path / "baseline.json"
        current = tmp_path / "current.json"
        report = {
            "suite_name": "S",
            "timestamp": "2024-01-01T00:00:00",
            "summary": {"total": 2, "passed": 2, "failed": 0, "skipped": 0, "pass_rate": 1.0, "avg_score": 0.9},
            "results": [
                {"test_case_id": "t1", "test_case_name": "A", "passed": True, "score": 0.9},
                {"test_case_id": "t2", "test_case_name": "B", "passed": True, "score": 0.9},
            ],
        }
        baseline.write_text(json.dumps(report), encoding="utf-8")
        current_report = {
            "suite_name": "S",
            "timestamp": "2024-01-02T00:00:00",
            "summary": {"total": 2, "passed": 2, "failed": 0, "skipped": 0, "pass_rate": 1.0, "avg_score": 0.92},
            "results": [
                {"test_case_id": "t1", "test_case_name": "A", "passed": True, "score": 0.92},
                {"test_case_id": "t2", "test_case_name": "B", "passed": True, "score": 0.92},
            ],
        }
        current.write_text(json.dumps(current_report), encoding="utf-8")
        result = runner.invoke(app, ["drift", str(baseline), str(current)])
        assert result.exit_code == 0
        assert "No regression" in result.output


class TestVersionCommand:
    """Tests for the ``version`` CLI command."""

    def test_version(self) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "EvalForge" in result.output
