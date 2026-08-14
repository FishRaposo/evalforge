"""Typed self-consistency and judge-calibration payloads."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class JudgeSample(BaseModel):
    """One normalized judge sample, including parse failures."""

    score: float = Field(default=0.0, ge=0.0, le=1.0)
    criterion_scores: dict[str, float] = Field(default_factory=dict)
    reasoning: str = ""
    method: str = "unknown"
    error: str | None = None
    provider: str | None = None
    model: str | None = None
    usage: dict[str, int] = Field(default_factory=dict)
    cache_hit: bool | None = None
    fallback_path: str | None = None

    @property
    def valid(self) -> bool:
        return self.error is None


class CalibrationSummary(BaseModel):
    """Deterministic aggregate for a set of judge samples."""

    sample_count: int = Field(ge=1)
    valid_sample_count: int = Field(ge=0)
    mean_score: float = Field(ge=0.0, le=1.0)
    standard_deviation: float = Field(default=0.0, ge=0.0)
    agreement: Literal["high", "medium", "low"] = "high"
    uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    samples: list[JudgeSample] = Field(default_factory=list)
    criterion_aggregates: dict[str, float] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)

    @property
    def stddev(self) -> float:
        """Compatibility alias for consumers that call this field ``stddev``."""

        return self.standard_deviation

    def as_details(self) -> dict[str, Any]:
        """Return the additive details shape used by ``JudgeResult``."""

        return {
            "sample_count": self.sample_count,
            "valid_sample_count": self.valid_sample_count,
            "samples": [sample.model_dump(mode="json") for sample in self.samples],
            "criterion_aggregates": self.criterion_aggregates,
            "standard_deviation": self.standard_deviation,
            "stddev": self.standard_deviation,
            "agreement": self.agreement,
            "uncertainty": self.uncertainty,
            "errors": self.errors,
        }


# Names used by early adopters of the calibration API.
CalibrationSample = JudgeSample
LLMJudgeSample = JudgeSample
