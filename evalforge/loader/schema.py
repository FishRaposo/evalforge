"""Pydantic schemas for YAML test suite file validation."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from evalforge.models.test_case import TestCaseType


class TestCaseFile(BaseModel):
    """Schema for an individual test case in a YAML file.

    Attributes:
        id: Unique identifier for the test case.
        name: Human-readable name.
        type: The evaluation type (must be a valid TestCaseType).
        input: The prompt or query string.
        expected: Expected result, can be string, null, or dict.
        metadata: Optional judge configuration.
        tags: Optional categorization tags.
    """

    id: str = Field(..., description="Unique test case identifier")
    name: str = Field(..., description="Human-readable test case name")
    type: TestCaseType = Field(..., description="Evaluation type")
    input: str = Field(..., description="Prompt to send to the AI system")
    expected: Optional[Any] = Field(None, description="Expected result")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Judge config")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")


class SuiteFile(BaseModel):
    """Schema for a complete YAML test suite file.

    Attributes:
        name: Suite name.
        description: Suite description.
        version: Suite version string.
        backend: Optional backend override.
        test_cases: List of test case definitions.
    """

    name: str = Field(..., description="Suite name")
    description: str = Field(default="", description="Suite description")
    version: str = Field(default="1.0", description="Suite version")
    backend: Optional[str] = Field(None, description="Backend override")
    test_cases: list[TestCaseFile] = Field(
        default_factory=list, description="Test cases"
    )
