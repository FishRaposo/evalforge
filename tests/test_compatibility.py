"""Contracts for EvalForge-owned compatibility interfaces."""

from __future__ import annotations

import asyncio
from pathlib import Path

from evalforge.compatibility import (
    Completion,
    DatasetRecord,
    LLMClientFactory,
    RegistryDriftEngine,
    RegistryJudgeEngine,
    SQLiteReportRepository,
)
from evalforge.models.report import Report, ReportSummary
from evalforge.models.test_case import TestCase, TestCaseType


def _case() -> TestCase:
    return TestCase(
        id="compat-1",
        name="Compatibility",
        type=TestCaseType.EXACT_ANSWER,
        input="capital",
        expected="Paris",
    )


def test_registry_judge_engine_preserves_builtin_exact_score() -> None:
    result = RegistryJudgeEngine().evaluate(_case(), "Paris")
    assert result.passed is True
    assert result.score == 1.0


def test_dataset_record_normalizes_common_fields() -> None:
    record = DatasetRecord.from_mapping(
        {"id": 3, "query": "q", "expected_answer": "a", "context": ["c"]}
    )
    assert record.id == "3"
    assert record.query == "q"
    assert record.expected_answer == "a"
    assert record.context == ["c"]


def test_client_factory_offline_completion_is_deterministic() -> None:
    factory = LLMClientFactory()
    client = factory.create(provider="openai", model="mock", api_key=None)
    first = asyncio.run(client.complete("hello"))
    second = asyncio.run(client.complete("hello"))
    assert isinstance(first, Completion)
    assert first == second
    assert first.metadata["fallback_path"] == "offline-simulated"


def test_client_factory_accepts_mocked_provider_client() -> None:
    class FakeClient:
        async def complete(self, prompt: str, **kwargs) -> Completion:
            return Completion(content="fixture", provider="fake", model="fixture")

    client = LLMClientFactory().create(provider="openai", client=FakeClient())
    result = asyncio.run(client.complete("prompt"))
    assert result.content == "fixture"
    assert result.provider == "fake"


def test_sqlite_report_repository_round_trips_history(tmp_path: Path) -> None:
    repository = SQLiteReportRepository(str(tmp_path / "history.db"))
    report = Report(
        suite_name="compat",
        summary=ReportSummary(
            total=1, passed=1, failed=0, pass_rate=1.0, avg_score=1.0
        ),
    )
    run_id = repository.save(report)
    assert repository.get(run_id)["suite_name"] == "compat"
    repository.set_baseline("compat", report)
    assert repository.get_baseline("compat")["suite_name"] == "compat"


def test_registry_drift_engine_delegates_to_existing_detector() -> None:
    report = Report(
        suite_name="compat",
        summary=ReportSummary(
            total=0, passed=0, failed=0, pass_rate=0.0, avg_score=0.0
        ),
    )
    result = RegistryDriftEngine().compare(report, report)
    assert result.suite_name == "compat"
