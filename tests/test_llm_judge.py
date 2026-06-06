"""Tests for LLMJudge and EnsembleJudge."""

from __future__ import annotations

import pytest

from evalforge.judges.exact_match import ExactMatchJudge
from evalforge.judges.llm_judge import EnsembleJudge, LLMJudge
from evalforge.models.test_case import TestCase, TestCaseType


class TestLLMJudge:
    """Tests for LLMJudge."""

    def test_default_criteria(self) -> None:
        judge = LLMJudge()
        assert "Accuracy" in judge._default_criteria()

    def test_build_prompt(self) -> None:
        judge = LLMJudge(criteria="Test criteria")
        prompt = judge._build_prompt("query_text", "response_text", "reference_context")
        assert "Test criteria" in prompt
        assert "query_text" in prompt
        assert "response_text" in prompt
        assert "reference_context" in prompt

    def test_simulated_evaluation(self) -> None:
        judge = LLMJudge()
        test_case = TestCase(
            id="t1",
            name="Test LLM",
            type=TestCaseType.SEMANTIC_ANSWER,
            input="hi",
            expected="hello",
        )
        result = judge.judge(test_case, "hello")
        assert result.score >= 0.5
        assert "simulated" in result.details.get("method", "")

    def test_parse_evaluation(self) -> None:
        judge = LLMJudge()
        content = (
            "score: 8.5\n"
            "justification: Very good response.\n"
            "accuracy: 9.0\n"
            "completeness: 8.0\n"
            "clarity: 8.5\n"
            "relevance: 9.0"
        )
        result = judge._parse_evaluation(content)
        assert result["score"] == 8.5
        assert result["reasoning"] == "Very good response."
        assert result["criteria_scores"]["accuracy"] == 9.0
        assert result["criteria_scores"]["completeness"] == 8.0
        assert result["criteria_scores"]["clarity"] == 8.5
        assert result["criteria_scores"]["relevance"] == 9.0


class TestEnsembleJudge:
    """Tests for EnsembleJudge."""

    def test_ensemble_single_judge(self) -> None:
        sub_judge = ExactMatchJudge()
        ensemble = EnsembleJudge(judges=[sub_judge])
        test_case = TestCase(
            id="t2",
            name="Test EM",
            type=TestCaseType.EXACT_ANSWER,
            input="Question",
            expected="Paris",
        )
        result = ensemble.judge(test_case, "Paris")
        assert result.passed is True
        assert result.score == 1.0

    def test_ensemble_multiple_judges(self) -> None:
        class FakeJudge1(ExactMatchJudge):
            def judge(self, test_case: TestCase, response: str):
                from evalforge.judges.base import JudgeResult
                return JudgeResult(passed=True, score=0.9, details={"method": "fake1"})

        class FakeJudge2(ExactMatchJudge):
            def judge(self, test_case: TestCase, response: str):
                from evalforge.judges.base import JudgeResult
                return JudgeResult(passed=True, score=0.7, details={"method": "fake2"})

        ensemble = EnsembleJudge(judges=[FakeJudge1(), FakeJudge2()], weights=[2.0, 1.0])
        test_case = TestCase(
            id="t3",
            name="Test Multi",
            type=TestCaseType.SEMANTIC_ANSWER,
            input="hi",
            expected="hello",
        )
        result = ensemble.judge(test_case, "hello")
        # Weighted avg: (0.9 * 2.0 + 0.7 * 1.0) / 3.0 = (1.8 + 0.7) / 3.0 = 2.5 / 3.0 = 0.833
        assert result.score == pytest.approx(0.833, abs=0.001)
        assert result.passed is True
        assert result.details["agreement"] == "medium"  # variance = 0.2
