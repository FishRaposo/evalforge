"""Tests for the custom judge plugin system."""

from __future__ import annotations

from pathlib import Path

import pytest

from evalforge.judges.base import JudgeResult
from evalforge.models.test_case import TestCase, TestCaseType
from evalforge.plugins import CustomJudge, load_judge_from_module


class TestCustomJudge:
    """Tests for CustomJudge."""

    def test_bool_result(self) -> None:
        judge = CustomJudge(lambda tc, resp: True, name="bool_judge")
        tc = TestCase(id="t1", name="Test", type=TestCaseType.EXACT_ANSWER, input="hi", expected="hi")
        result = judge.judge(tc, "hi")
        assert result.passed is True
        assert result.score == 1.0

    def test_dict_result(self) -> None:
        judge = CustomJudge(lambda tc, resp: {"passed": True, "score": 0.95}, name="dict_judge")
        tc = TestCase(id="t1", name="Test", type=TestCaseType.EXACT_ANSWER, input="hi", expected="hi")
        result = judge.judge(tc, "hi")
        assert result.passed is True
        assert result.score == 0.95

    def test_judgeresult_result(self) -> None:
        judge = CustomJudge(lambda tc, resp: JudgeResult(passed=True, score=0.8), name="jr_judge")
        tc = TestCase(id="t1", name="Test", type=TestCaseType.EXACT_ANSWER, input="hi", expected="hi")
        result = judge.judge(tc, "hi")
        assert result.passed is True

    def test_exception_handling(self) -> None:
        def _bad(tc: TestCase, resp: str) -> bool:
            raise RuntimeError("boom")

        judge = CustomJudge(_bad, name="bad_judge")
        tc = TestCase(id="t1", name="Test", type=TestCaseType.EXACT_ANSWER, input="hi", expected="hi")
        result = judge.judge(tc, "hi")
        assert result.passed is False
        assert result.score == 0.0
        assert "boom" in result.details["error"]


class TestLoadJudgeFromModule:
    """Tests for load_judge_from_module."""

    def test_load_valid_module(self, tmp_path: Path) -> None:
        mod = tmp_path / "my_judge.py"
        mod.write_text(
            "def judge(test_case, response):\n    return True\n",
            encoding="utf-8",
        )
        judge = load_judge_from_module(str(mod), judge_name="my_judge")
        assert judge._name == "my_judge"
        tc = TestCase(id="t1", name="Test", type=TestCaseType.EXACT_ANSWER, input="hi", expected="hi")
        result = judge.judge(tc, "hi")
        assert result.passed is True

    def test_missing_judge_function(self, tmp_path: Path) -> None:
        mod = tmp_path / "bad_judge.py"
        mod.write_text("x = 1\n", encoding="utf-8")
        with pytest.raises(AttributeError):
            load_judge_from_module(str(mod))

    def test_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_judge_from_module("/nonexistent/judge.py")
