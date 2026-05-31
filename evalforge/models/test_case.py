"""Test case and test suite models."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class TestCaseType(str, Enum):
    """Supported test case evaluation types.

    Each type maps to a specific judge that handles the evaluation logic.
    """

    EXACT_ANSWER = "exact_answer"
    SEMANTIC_ANSWER = "semantic_answer"
    MUST_CITE = "must_cite"
    MUST_REFUSE = "must_refuse"
    MUST_RETRIEVE = "must_retrieve"
    FORBIDDEN_CONTENT = "forbidden_content"
    STRUCTURED_OUTPUT = "structured_output"


class TestCase(BaseModel):
    """A single test case defining an expected AI behavior.

    Attributes:
        id: Unique identifier for the test case.
        name: Human-readable name for the test case.
        type: The evaluation type determining which judge to use.
        input: The prompt or query to send to the AI system.
        expected: The expected result. Can be a string for simple matches
            or a dict for structured expectations like citations.
        metadata: Optional metadata for judge configuration (thresholds, etc.).
        tags: Optional tags for categorizing and filtering test cases.
    """

    id: str = Field(..., description="Unique test case identifier")
    name: str = Field(..., description="Human-readable test case name")
    type: TestCaseType = Field(..., description="Evaluation type")
    input: str = Field(..., description="Prompt to send to the AI system")
    expected: Optional[Any] = Field(
        None, description="Expected result (string or structured dict)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Optional judge configuration"
    )
    tags: list[str] = Field(default_factory=list, description="Categorization tags")


class TestSuite(BaseModel):
    """A collection of test cases forming a complete evaluation suite.

    Attributes:
        name: The name of the test suite.
        description: A brief description of what the suite evaluates.
        version: Semantic version of the test suite.
        backend: Optional backend override for this suite.
        test_cases: The list of test cases to evaluate.
    """

    name: str = Field(..., description="Suite name")
    description: str = Field(default="", description="Suite description")
    version: str = Field(default="1.0", description="Suite version")
    backend: Optional[str] = Field(None, description="Backend override for this suite")
    test_cases: list[TestCase] = Field(
        default_factory=list, description="Test cases in this suite"
    )
