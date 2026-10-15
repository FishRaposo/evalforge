"""Abstract base class and result model for evaluation judges."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
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

    def judge_with_context(
        self,
        test_case: TestCase,
        response: str,
        backend_metadata: Mapping[str, Any] | None = None,
    ) -> JudgeResult:
        """Evaluate a response with the backend's response metadata available.

        Runners call this so judges that need structured backend output (for
        example ``retrieved_ids`` for the retrieval judge) can read it. The
        default ignores the metadata and delegates to :meth:`judge`.

        Args:
            test_case: The test case defining expected behavior.
            response: The actual AI response to evaluate.
            backend_metadata: ``BackendResponse.metadata`` for this response.

        Returns:
            A JudgeResult with pass status, score, and details.
        """
        return self.judge(test_case, response)
