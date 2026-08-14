"""EvalForge-owned contracts used at provider and persistence boundaries."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from evalforge.judges.base import JudgeResult
from evalforge.models.report import Report
from evalforge.models.test_case import TestCase


class Completion(BaseModel):
    """Provider-neutral completion with additive operational metadata."""

    content: str
    provider: str = "unknown"
    model: str | None = None
    usage: dict[str, int] = Field(default_factory=dict)
    cache_hit: bool = False
    fallback_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class LLMClient(Protocol):
    async def complete(
        self,
        prompt: str,
        *,
        context: Mapping[str, Any] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> Completion:
        """Return a provider-neutral completion."""
        ...


class DatasetRecord(BaseModel):
    """Canonical record shape for local and remote dataset sources."""

    id: str
    query: str
    expected_answer: Any = ""
    context: Any = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_mapping(
        cls, item: Mapping[str, Any], index: int | None = None
    ) -> "DatasetRecord":
        record_id = item.get("id", index if index is not None else "record")
        return cls(
            id=str(record_id),
            query=str(item.get("query", item.get("question", ""))),
            expected_answer=item.get("expected_answer", item.get("answer", "")),
            context=item.get("context"),
            metadata=dict(item.get("metadata", {}))
            if isinstance(item.get("metadata", {}), Mapping)
            else {},
        )


@runtime_checkable
class DatasetSource(Protocol):
    async def load_records(
        self,
        name: str,
        *,
        split: str = "validation",
        max_samples: int | None = None,
    ) -> list[DatasetRecord]:
        """Load normalized dataset records."""
        ...


@runtime_checkable
class JudgeEngine(Protocol):
    def evaluate(self, test_case: TestCase, response: str) -> JudgeResult:
        """Evaluate using EvalForge's registered judge."""
        ...


@runtime_checkable
class DriftEngine(Protocol):
    def compare(self, baseline: Report, current: Report) -> Any:
        """Compare two reports and return a drift result."""
        ...


@runtime_checkable
class ReportRepository(Protocol):
    def save(self, report: Report | Mapping[str, Any]) -> int:
        """Persist a report and return its identifier."""
        ...

    def get(self, run_id: int) -> dict[str, Any] | None:
        """Fetch one persisted report row."""
        ...

    def list(
        self, suite_name: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """List persisted reports."""
        ...

    def set_baseline(self, suite_name: str, report: Report | Mapping[str, Any]) -> None:
        """Persist a suite baseline."""
        ...

    def get_baseline(self, suite_name: str) -> dict[str, Any] | None:
        """Fetch a suite baseline."""
        ...


class RunMetadata(BaseModel):
    """Shared timestamp metadata for adapter receipts."""

    created_at: datetime
