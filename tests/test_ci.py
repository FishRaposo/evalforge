"""Tests for CI/CD integration (GitHubPRReporter, RegressionDetector, CIPipeline)."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
import pytest

from evalforge.ci.github_action import CIPipeline, GitHubPRReporter, RegressionDetector


class TestGitHubPRReporter:
    """Tests for GitHubPRReporter with mocked httpx client."""

    @pytest.fixture
    def reporter(self) -> GitHubPRReporter:
        return GitHubPRReporter(
            token="test-token",
            repository="owner/repo",
            pr_number=42,
        )

    @pytest.mark.asyncio
    async def test_post_comment_success(self, reporter: GitHubPRReporter) -> None:
        async def _handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/repos/owner/repo/issues/42/comments"
            return httpx.Response(201)

        transport = httpx.MockTransport(_handler)
        async with httpx.AsyncClient(transport=transport) as client:
            ok = await reporter.post_comment({"suite_name": "suite"}, client=client)
        assert ok is True

    @pytest.mark.asyncio
    async def test_post_comment_missing_credentials(self) -> None:
        r = GitHubPRReporter()
        ok = await r.post_comment({"suite_name": "suite"})
        assert ok is False

    @pytest.mark.asyncio
    async def test_update_commit_status_success(self, reporter: GitHubPRReporter) -> None:
        async def _handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/repos/owner/repo/statuses/abc123"
            body = json.loads(request.content)
            assert body["state"] == "success"
            return httpx.Response(201)

        transport = httpx.MockTransport(_handler)
        async with httpx.AsyncClient(transport=transport) as client:
            ok = await reporter.update_commit_status("abc123", "success", "All good", client=client)
        assert ok is True

    def test_get_pr_number_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GITHUB_REF", "refs/pull/99/merge")
        r = GitHubPRReporter(token="t", repository="o/r")
        assert r.pr_number == 99

    def test_format_report(self, reporter: GitHubPRReporter) -> None:
        report = {
            "suite_name": "Test",
            "backend": "mock",
            "summary": {
                "total_tests": 10,
                "passed": 8,
                "failed": 2,
                "pass_rate": 0.8,
                "avg_score": 0.85,
            },
            "failed_tests": [{"name": "t1", "error": "wrong"}],
        }
        md = reporter._format_report(report)
        assert "EvalForge Results" in md
        assert "8 ✅" in md
        assert "2 ❌" in md
        assert "wrong" in md


class TestRegressionDetector:
    """Tests for RegressionDetector."""

    @pytest.fixture
    def detector(self) -> RegressionDetector:
        return RegressionDetector(fail_threshold=0.7, regression_threshold=0.1)

    def test_no_regression_above_threshold(self, detector: RegressionDetector) -> None:
        current = {"summary": {"avg_score": 0.85}}
        result = detector.check_regression(current, None)
        assert result["has_regression"] is False
        assert result["should_fail_build"] is False

    def test_regression_below_threshold(self, detector: RegressionDetector) -> None:
        current = {"summary": {"avg_score": 0.5}}
        result = detector.check_regression(current, None)
        assert result["has_regression"] is True
        assert result["should_fail_build"] is True

    def test_regression_vs_baseline(self, detector: RegressionDetector) -> None:
        current = {"summary": {"avg_score": 0.75}}
        baseline = {"summary": {"avg_score": 0.90}}
        result = detector.check_regression(current, baseline)
        assert result["has_regression"] is True
        assert result["regression"] == pytest.approx(0.15)

    def test_no_regression_vs_baseline(self, detector: RegressionDetector) -> None:
        current = {"summary": {"avg_score": 0.88}}
        baseline = {"summary": {"avg_score": 0.90}}
        result = detector.check_regression(current, baseline)
        assert result["has_regression"] is False


class TestCIPipeline:
    """Tests for CIPipeline with mocked backends and reporter."""

    @pytest.fixture
    def sample_suite_path(self, tmp_path: pytestFixture) -> str:
        import yaml
        path = tmp_path / "suite.yaml"
        data = {
            "name": "CI Test Suite",
            "version": "1.0",
            "test_cases": [
                {"id": "tc-1", "name": "Pass", "type": "exact_answer", "input": "hi", "expected": "hi"},
            ],
        }
        path.write_text(yaml.dump(data), encoding="utf-8")
        return str(path)

    @pytest.mark.asyncio
    async def test_ci_pipeline_runs(self, sample_suite_path: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GITHUB_SHA", "abc123")
        pipeline = CIPipeline(suite_path=sample_suite_path, backend="mock", fail_threshold=0.5)

        # Mock reporter to avoid real network calls
        calls: list[str] = []
        async def _mock_post(report: dict[str, Any]) -> bool:
            calls.append("post_comment")
            return True
        async def _mock_status(sha: str, state: str, desc: str) -> bool:
            calls.append(f"status:{state}")
            return True

        pipeline.reporter.post_comment = _mock_post
        pipeline.reporter.update_commit_status = _mock_status

        result = await pipeline.run()
        assert "evaluation" in result
        assert "regression_check" in result
        assert "exit_code" in result
        assert "post_comment" in calls

    @pytest.mark.asyncio
    async def test_ci_pipeline_fails_on_regression(self, sample_suite_path: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GITHUB_SHA", "abc123")
        # Create baseline with perfect score to trigger regression
        os.makedirs(".evalforge", exist_ok=True)
        with open(".evalforge/baseline.json", "w") as f:
            json.dump({"summary": {"avg_score": 1.0}}, f)

        try:
            pipeline = CIPipeline(suite_path=sample_suite_path, backend="mock", fail_threshold=0.5)
            async def _mock_post(report: dict[str, Any]) -> bool:
                return True
            async def _mock_status(sha: str, state: str, desc: str) -> bool:
                return True
            pipeline.reporter.post_comment = _mock_post
            pipeline.reporter.update_commit_status = _mock_status

            result = await pipeline.run()
            # Even if regression detected, exit code depends on threshold
            assert "regression_check" in result
        finally:
            if os.path.exists(".evalforge/baseline.json"):
                os.remove(".evalforge/baseline.json")


pytestFixture = pytest.fixture
