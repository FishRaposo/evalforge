"""Abstract base class and result model for evaluation judges."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from evalforge.models.test_case import TestCase


class JudgeResult(BaseModel):
    """Result from a judge evaluation.

    Attributes:
        passed: Whether the response passed the evaluation.
        score: Numerical score from 0.0 to 1.0.
        details: Additional details about the evaluation.
    """

    passed: bool = Field(..., description="Whether evaluation passed")
    score: float = Field(..., ge=0.0, le=1.0, description="Judge score")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Evaluation details"
    )


class BaseJudge(ABC):
    """Abstract base class for all evaluation judges.

    Judges evaluate AI responses against expected behavior and return
    structured results with pass/fail status, scores, and details.
    """

    @abstractmethod
    def judge(self, test_case: TestCase, response: str) -> JudgeResult:
        """Evaluate a response against the test case expectations.

        Args:
            test_case: The test case defining expected behavior.
            response: The actual AI response to evaluate.

        Returns:
            A JudgeResult with pass status, score, and details.
        """
        ...
