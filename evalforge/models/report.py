"""Report models for evaluation output."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from evalforge.models.test_result import TestResult


class ReportSummary(BaseModel):
    """Summary statistics for a test suite evaluation.

    Attributes:
        total: Total number of test cases.
        passed: Number of passed test cases.
        failed: Number of failed test cases.
        skipped: Number of skipped test cases.
        pass_rate: Ratio of passed to total test cases.
        avg_score: Average judge score across all test cases.
    """

    total: int = Field(..., description="Total test cases")
    passed: int = Field(..., description="Passed test cases")
    failed: int = Field(..., description="Failed test cases")
    skipped: int = Field(default=0, description="Skipped test cases")
    pass_rate: float = Field(..., ge=0.0, le=1.0, description="Pass rate ratio")
    avg_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Average score")


class Report(BaseModel):
    """Complete evaluation report with results and metadata.

    Attributes:
        suite_name: Name of the evaluated test suite.
        timestamp: When the report was generated.
        summary: Aggregated summary statistics.
        results: Individual test case results.
        metadata: Additional report metadata (backend, config, etc.).
    """

    suite_name: str = Field(..., description="Evaluated suite name")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Report generation time"
    )
    summary: ReportSummary = Field(..., description="Aggregated summary")
    results: list[TestResult] = Field(
        default_factory=list, description="Individual test results"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class _FrozenDict(dict):
    """JSON-compatible mapping used only for completed saved snapshots."""

    def _deny(self, *args: Any, **kwargs: Any) -> Any:
        raise TypeError("Completed evaluation report is immutable")

    __setitem__ = __delitem__ = clear = pop = popitem = __ior__ = _deny

    def setdefault(self, key: Any, default: Any = None) -> Any:
        return self._deny()

    def update(self, *args: Any, **kwargs: Any) -> None:
        self._deny()


class _FrozenList(list):
    """JSON-compatible sequence used only for completed saved snapshots."""

    def _deny(self, *args: Any, **kwargs: Any) -> Any:
        raise TypeError("Completed evaluation report is immutable")

    __setitem__ = __delitem__ = append = clear = extend = insert = pop = remove = (
        reverse
    ) = __iadd__ = __imul__ = _deny

    def sort(self, *args: Any, **kwargs: Any) -> None:
        self._deny()


class _FrozenSummary(ReportSummary):
    model_config = ConfigDict(frozen=True)


class _FrozenResult(TestResult):
    model_config = ConfigDict(frozen=True)


class _FrozenReport(Report):
    model_config = ConfigDict(frozen=True)


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return _FrozenDict({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return _FrozenList(_freeze(item) for item in value)
    return value


def immutable_report(report: Report) -> Report:
    """Detach and freeze a completed report while preserving legacy JSON schema."""
    results = []
    for result in report.results:
        snapshot = _FrozenResult.model_validate(result.model_dump(mode="python"))
        results.append(
            snapshot.model_copy(
                update={
                    "judge_details": _freeze(snapshot.judge_details),
                    "backend_metadata": _freeze(snapshot.backend_metadata),
                }
            )
        )
    return _FrozenReport.model_construct(
        suite_name=report.suite_name,
        timestamp=report.timestamp,
        summary=_FrozenSummary.model_validate(report.summary.model_dump()),
        results=_FrozenList(results),
        metadata=_freeze(report.metadata),
    )
