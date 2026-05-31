"""Test result models for evaluation outcomes."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class TestResult(BaseModel):
    """Result of evaluating a single test case.

    Attributes:
        test_case_id: The ID of the evaluated test case.
        test_case_name: The human-readable name of the test case.
        passed: Whether the test case passed evaluation.
        score: Numerical score from the judge (0.0 to 1.0).
        actual_response: The raw response from the AI backend.
        judge_details: Detailed output from the judge for debugging.
        execution_time_ms: Time taken to execute the test in milliseconds.
        error: Error message if the test failed due to an exception.
    """

    test_case_id: str = Field(..., description="Evaluated test case ID")
    test_case_name: str = Field(default="", description="Test case name")
    passed: bool = Field(..., description="Whether evaluation passed")
    score: float = Field(..., ge=0.0, le=1.0, description="Judge score (0.0-1.0)")
    actual_response: str = Field(default="", description="Raw AI backend response")
    judge_details: dict[str, Any] = Field(
        default_factory=dict, description="Judge evaluation details"
    )
    execution_time_ms: float = Field(
        default=0.0, description="Execution time in milliseconds"
    )
    error: Optional[str] = Field(None, description="Error message if test failed")


class TestRunResult(BaseModel):
    """Aggregated results from running an entire test suite.

    Attributes:
        suite_name: Name of the evaluated test suite.
        total: Total number of test cases evaluated.
        passed: Number of test cases that passed.
        failed: Number of test cases that failed.
        results: Individual test results.
        started_at: Timestamp when the suite run started.
        completed_at: Timestamp when the suite run completed.
    """

    suite_name: str = Field(..., description="Evaluated suite name")
    total: int = Field(..., description="Total test cases")
    passed: int = Field(..., description="Passed test cases")
    failed: int = Field(..., description="Failed test cases")
    results: list[TestResult] = Field(
        default_factory=list, description="Individual test results"
    )
    started_at: datetime = Field(
        default_factory=datetime.now, description="Suite start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        None, description="Suite completion timestamp"
    )
