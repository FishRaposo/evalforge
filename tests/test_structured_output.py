"""Tests for the StructuredOutputJudge."""

from __future__ import annotations

from typing import Any

from evalforge.judges.base import JudgeResult
from evalforge.models.test_case import TestCase, TestCaseType


class TestStructuredOutputJudge:
    """Tests for StructuredOutputJudge."""

    def _make_judge(self) -> Any:
        from evalforge.judges.structured_output import StructuredOutputJudge

        return StructuredOutputJudge()

    def test_valid_json_all_required_fields(self) -> None:
        judge = self._make_judge()
        test_case = TestCase(
            id="so-001",
            name="Valid structured output",
            type=TestCaseType.STRUCTURED_OUTPUT,
            input="Return user profile as JSON",
            expected={
                "fields": {"name": "Alice", "age": 30, "email": "alice@example.com"},
                "types": {"name": "str", "age": "int", "email": "str"},
            },
        )
        response = '{"name": "Alice", "age": 30, "email": "alice@example.com"}'

        result = judge.judge(test_case, response)

        assert result.passed is True
        assert result.score == 1.0

    def test_missing_required_fields(self) -> None:
        judge = self._make_judge()
        test_case = TestCase(
            id="so-002",
            name="Missing fields",
            type=TestCaseType.STRUCTURED_OUTPUT,
            input="Return user profile as JSON",
            expected={
                "fields": {"name": "Alice", "age": 30, "email": "alice@example.com"},
                "types": {"name": "str", "age": "int", "email": "str"},
            },
        )
        response = '{"name": "Alice"}'

        result = judge.judge(test_case, response)

        assert result.passed is False
        assert result.score < 1.0
        assert "missing_fields" in result.details

    def test_wrong_field_types(self) -> None:
        judge = self._make_judge()
        test_case = TestCase(
            id="so-003",
            name="Wrong types",
            type=TestCaseType.STRUCTURED_OUTPUT,
            input="Return user profile as JSON",
            expected={
                "fields": {"name": "Alice", "age": 30},
                "types": {"name": "str", "age": "int"},
            },
        )
        response = '{"name": "Alice", "age": "thirty"}'

        result = judge.judge(test_case, response)

        assert result.passed is False
        assert result.score < 1.0
        assert "type_mismatches" in result.details

    def test_non_json_response(self) -> None:
        judge = self._make_judge()
        test_case = TestCase(
            id="so-004",
            name="Non-JSON response",
            type=TestCaseType.STRUCTURED_OUTPUT,
            input="Return user profile as JSON",
            expected={
                "fields": {"name": "Alice"},
                "types": {"name": "str"},
            },
        )
        response = "This is not JSON at all."

        result = judge.judge(test_case, response)

        assert result.passed is False
        assert result.score == 0.0
        assert "parse_error" in result.details

    def test_partial_match(self) -> None:
        judge = self._make_judge()
        test_case = TestCase(
            id="so-005",
            name="Partial match",
            type=TestCaseType.STRUCTURED_OUTPUT,
            input="Return user profile as JSON",
            expected={
                "fields": {"name": "Alice", "age": 30, "email": "alice@example.com"},
                "types": {"name": "str", "age": "int", "email": "str"},
            },
        )
        response = '{"name": "Alice", "age": 30, "email": "bob@example.com"}'

        result = judge.judge(test_case, response)

        assert 0.0 < result.score < 1.0

    def test_empty_expected_fields(self) -> None:
        judge = self._make_judge()
        test_case = TestCase(
            id="so-006",
            name="Empty expected",
            type=TestCaseType.STRUCTURED_OUTPUT,
            input="Return anything as JSON",
            expected={"fields": {}, "types": {}},
        )
        response = '{"arbitrary": "data"}'

        result = judge.judge(test_case, response)

        assert result.passed is True
        assert result.score == 1.0
