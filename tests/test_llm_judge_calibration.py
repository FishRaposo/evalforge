"""Calibration and self-consistency contracts for the LLM judge."""

from __future__ import annotations

import pytest

from evalforge.judges.llm_judge import LLMJudge
from evalforge.models.test_case import TestCase, TestCaseType


def _case(case_id: str = "calibration") -> TestCase:
    return TestCase(
        id=case_id,
        name="Calibration case",
        type=TestCaseType.SEMANTIC_ANSWER,
        input="What is two plus two?",
        expected="four",
    )


def test_num_samples_must_be_positive() -> None:
    with pytest.raises(ValueError, match="num_samples"):
        LLMJudge(num_samples=0)


def test_simulation_runs_exactly_num_samples_and_reports_calibration() -> None:
    result = LLMJudge(num_samples=3).judge(_case("stable"), "four")

    assert result.details["sample_count"] == 3
    assert len(result.details["samples"]) == 3
    assert result.details["valid_sample_count"] == 3
    assert set(result.details["criterion_aggregates"]) >= {
        "accuracy",
        "completeness",
        "clarity",
        "relevance",
    }
    assert 0.0 <= result.details["uncertainty"] <= 1.0


def test_simulation_is_stable_across_judge_instances() -> None:
    first = LLMJudge(num_samples=4).judge(_case("stable"), "four")
    second = LLMJudge(num_samples=4).judge(_case("stable"), "four")

    assert first.score == second.score
    assert first.details["samples"] == second.details["samples"]


def test_real_mode_calls_evaluator_exactly_num_samples(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EVALFORGE_LLM_MODE", "real")
    judge = LLMJudge(num_samples=3)
    calls: list[int] = []

    def fake_evaluate(query: str, response: str, context=None):
        calls.append(len(calls))
        return {
            "score": 7.0 + len(calls),
            "reasoning": "structured sample",
            "criteria_scores": {"accuracy": 8.0},
            "method": "llm_single",
        }

    monkeypatch.setattr(judge, "_evaluate_sync", fake_evaluate)
    result = judge.judge(_case("real"), "four")

    assert calls == [0, 1, 2]
    assert result.details["sample_count"] == 3
    assert result.details["valid_sample_count"] == 3
    assert result.score == pytest.approx((0.8 + 0.9 + 1.0) / 3)


def test_structured_json_and_fenced_json_are_preferred() -> None:
    judge = LLMJudge()
    structured = judge._parse_evaluation(
        '```json\n{"score": 0.8, "reasoning": "clear", '
        '"criteria_scores": {"accuracy": 0.9}, "method": "json"}\n```'
    )

    assert structured["score"] == pytest.approx(0.8)
    assert structured["reasoning"] == "clear"
    assert structured["criteria_scores"]["accuracy"] == pytest.approx(0.9)
    assert structured["method"] == "json"


def test_structured_sample_with_invalid_score_is_explicitly_malformed() -> None:
    parsed = LLMJudge()._parse_evaluation(
        '{"score": "not-a-number", "reasoning": "invalid"}'
    )

    assert parsed["error"] == "Malformed evaluation output"


def test_malformed_real_samples_are_explicit_and_do_not_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EVALFORGE_LLM_MODE", "real")
    judge = LLMJudge(num_samples=2)
    monkeypatch.setattr(
        judge,
        "_evaluate_sync",
        lambda query, response, context=None: {
            "score": 0.0,
            "error": "malformed structured output",
            "method": "llm_single",
        },
    )

    result = judge.judge(_case("invalid"), "four")

    assert result.passed is False
    assert result.score == 0.0
    assert result.details["valid_sample_count"] == 0
    assert result.details["errors"] == [
        "malformed structured output",
        "malformed structured output",
    ]


def test_real_provider_metadata_is_preserved_in_sample_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EVALFORGE_LLM_MODE", "real")
    judge = LLMJudge()

    async def fake_factory(prompt: str):
        return {
            "score": 8.0,
            "reasoning": "provider fixture",
            "criteria_scores": {"accuracy": 8.0},
            "method": "json",
            "provider": "openai",
            "model": "fixture-model",
            "usage": {"total_tokens": 12},
            "fallback_path": None,
            "cache_hit": False,
        }

    monkeypatch.setattr(judge, "_evaluate_with_factory", fake_factory)
    result = judge.judge(_case("provider"), "four")

    sample = result.details["samples"][0]
    assert sample["provider"] == "openai"
    assert sample["model"] == "fixture-model"
    assert sample["usage"] == {"total_tokens": 12}
