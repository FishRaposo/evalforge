"""Tests for the custom-judge plugin loader wiring into the runner.

Covers ``resolve_judge_override`` and the ``RAGRunner`` ``judge_overrides``
hook that lets a user-defined plugin replace a judge for a single test-case
type without mutating the global registry.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from evalforge.backends.mock import MockBackend
from evalforge.judges.base import JudgeResult
from evalforge.models.test_case import TestCase, TestCaseType, TestSuite
from evalforge.plugins import CustomJudge, resolve_judge_override
from evalforge.runners.rag_runner import RAGRunner

_ALWAYS_PASS = (
    "def judge(test_case, response):\n    return {'passed': True, 'score': 1.0}\n"
)
_ALWAYS_FAIL = (
    "def judge(test_case, response):\n    return {'passed': False, 'score': 0.0}\n"
)


def _write_plugin(tmp_path: Path, body: str, name: str = "plugin.py") -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def _semantic_suite() -> TestSuite:
    return TestSuite(
        name="Plugin Suite",
        version="1.0",
        test_cases=[
            TestCase(
                id="p1",
                name="Semantic",
                type=TestCaseType.SEMANTIC_ANSWER,
                input="Explain gravity",
                expected="Gravity attracts objects with mass",
            )
        ],
    )


class TestResolveJudgeOverride:
    def test_resolves_string_type(self, tmp_path: Path) -> None:
        plugin = _write_plugin(tmp_path, _ALWAYS_PASS)
        judge_type, judge = resolve_judge_override(str(plugin), "semantic_answer")
        assert judge_type is TestCaseType.SEMANTIC_ANSWER
        assert isinstance(judge, CustomJudge)

    def test_resolves_enum_type(self, tmp_path: Path) -> None:
        plugin = _write_plugin(tmp_path, _ALWAYS_PASS)
        judge_type, judge = resolve_judge_override(
            str(plugin), TestCaseType.EXACT_ANSWER, judge_name="my_judge"
        )
        assert judge_type is TestCaseType.EXACT_ANSWER
        assert judge._name == "my_judge"

    def test_invalid_type_raises(self, tmp_path: Path) -> None:
        plugin = _write_plugin(tmp_path, _ALWAYS_PASS)
        with pytest.raises(ValueError, match="Unknown judge type"):
            resolve_judge_override(str(plugin), "not_a_real_type")

    def test_missing_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            resolve_judge_override("/nonexistent/plugin.py", "semantic_answer")


class TestRunnerJudgeOverrides:
    @pytest.mark.asyncio
    async def test_override_replaces_default_judge(self, tmp_path: Path) -> None:
        plugin = _write_plugin(tmp_path, _ALWAYS_PASS)
        judge_type, judge = resolve_judge_override(str(plugin), "semantic_answer")
        runner = RAGRunner(backend=MockBackend(), judge_overrides={judge_type: judge})
        results = await runner.run_suite(_semantic_suite())
        # The mock backend's default response would never match semantically,
        # but the always-pass override forces a pass.
        assert results[0].passed is True
        assert results[0].score == 1.0

    @pytest.mark.asyncio
    async def test_override_does_not_leak_to_other_runner(self, tmp_path: Path) -> None:
        plugin = _write_plugin(tmp_path, _ALWAYS_FAIL)
        judge_type, judge = resolve_judge_override(str(plugin), "semantic_answer")
        overridden = RAGRunner(
            backend=MockBackend(), judge_overrides={judge_type: judge}
        )
        plain = RAGRunner(backend=MockBackend())
        # Overridden runner uses the custom (always-fail) judge.
        forced = await overridden.run_suite(_semantic_suite())
        assert forced[0].passed is False
        # A separate runner without overrides keeps the registry default judge.
        assert TestCaseType.SEMANTIC_ANSWER in plain._judges
        assert not isinstance(plain._judges[TestCaseType.SEMANTIC_ANSWER], CustomJudge)

    @pytest.mark.asyncio
    async def test_override_judge_exception_is_contained(self, tmp_path: Path) -> None:
        body = "def judge(test_case, response):\n    raise RuntimeError('boom')\n"
        plugin = _write_plugin(tmp_path, body)
        judge_type, judge = resolve_judge_override(str(plugin), "semantic_answer")
        runner = RAGRunner(backend=MockBackend(), judge_overrides={judge_type: judge})
        results = await runner.run_suite(_semantic_suite())
        assert results[0].passed is False
        assert results[0].score == 0.0


def test_custom_judge_returns_judgeresult_passthrough() -> None:
    judge = CustomJudge(lambda tc, r: JudgeResult(passed=True, score=0.42))
    tc = TestCase(
        id="x",
        name="x",
        type=TestCaseType.SEMANTIC_ANSWER,
        input="q",
        expected="e",
    )
    result = judge.judge(tc, "r")
    assert result.score == 0.42
