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

    def test_real_mode_normalizes_score_to_unit_range(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Real-mode 1-10 scores normalize to [0,1] so JudgeResult validates."""
        monkeypatch.setenv("EVALFORGE_LLM_MODE", "real")
        judge = LLMJudge()

        # Simulate a real LLM parse: score on a 1-10 scale plus criteria scores.
        def _fake_evaluate_sync(query, response, context=None):
            return {
                "score": 8.5,
                "reasoning": "good",
                "criteria_scores": {"accuracy": 9.0, "clarity": 7.0},
                "method": "llm_single",
            }

        monkeypatch.setattr(judge, "_evaluate_sync", _fake_evaluate_sync)

        test_case = TestCase(
            id="t-real",
            name="Real mode",
            type=TestCaseType.SEMANTIC_ANSWER,
            input="hi",
            expected="hello",
        )
        result = judge.judge(test_case, "hello")

        # Must not raise pydantic ValidationError and stay within [0, 1].
        assert 0.0 <= result.score <= 1.0
        assert result.score == pytest.approx(0.85)
        assert result.passed is True
        # criteria_scores also normalized to [0, 1].
        assert result.details["criteria_scores"]["accuracy"] == pytest.approx(0.9)
        assert result.details["criteria_scores"]["clarity"] == pytest.approx(0.7)

    def test_real_mode_clamps_out_of_range_score(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A score above 10 (or below 0) is clamped into [0,1] rather than raising."""
        monkeypatch.setenv("EVALFORGE_LLM_MODE", "real")
        judge = LLMJudge()

        monkeypatch.setattr(
            judge,
            "_evaluate_sync",
            lambda query, response, context=None: {"score": 12.0},
        )

        test_case = TestCase(
            id="t-clamp",
            name="Clamp mode",
            type=TestCaseType.SEMANTIC_ANSWER,
            input="hi",
            expected="hello",
        )
        result = judge.judge(test_case, "hello")
        assert result.score == 1.0
        assert result.passed is True

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

        ensemble = EnsembleJudge(
            judges=[FakeJudge1(), FakeJudge2()], weights=[2.0, 1.0]
        )
        test_case = TestCase(
            id="t3",
            name="Test Multi",
            type=TestCaseType.SEMANTIC_ANSWER,
            input="hi",
            expected="hello",
        )
        result = ensemble.judge(test_case, "hello")
        # Weighted avg: (0.9 * 2.0 + 0.7 * 1.0) / 3.0
        # = (1.8 + 0.7) / 3.0 = 2.5 / 3.0 = 0.833
        assert result.score == pytest.approx(0.833, abs=0.001)
        assert result.passed is True
        assert result.details["agreement"] == "medium"  # variance = 0.2
