"""Report models for evaluation output."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

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
    avg_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Average score"
    )


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
