"""Structured output judge for validating JSON responses."""

from __future__ import annotations

import json
from typing import Any

from evalforge.judges.base import BaseJudge, JudgeResult
from evalforge.models.test_case import TestCase

_PYTHON_TYPE_MAP: dict[str, tuple[type, ...]] = {
    "str": (str,),
    "int": (int,),
    "float": (float,),
    "bool": (bool,),
    "list": (list,),
    "dict": (dict,),
    "string": (str,),
    "number": (int, float),
    "integer": (int,),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict,),
}


class StructuredOutputJudge(BaseJudge):
    """Judge that validates JSON responses against expected field schemas.

    Checks that all expected fields are present with correct values and types.
    Score is the ratio of fields that pass both value and type validation.

    Expected format in test_case.expected:
        {
            "fields": {"name": "Alice", "age": 30},
            "types": {"name": "str", "age": "int"}
        }
    """

    def judge(self, test_case: TestCase, response: str) -> JudgeResult:
        expected = test_case.expected if isinstance(test_case.expected, dict) else {}
        fields_spec: dict[str, Any] = expected.get("fields", {})
        types_spec: dict[str, str] = expected.get("types", {})

        parsed, parse_error = self._parse_json(response)
        if parse_error is not None:
            return JudgeResult(
                passed=False,
                score=0.0,
                details={
                    "match_type": "structured_output",
                    "parse_error": parse_error,
                },
            )

        field_results: dict[str, dict[str, Any]] = {}
        missing_fields: list[str] = []
        type_mismatches: list[str] = []
        value_mismatches: list[str] = []

        total = len(fields_spec) if fields_spec else 0
        if total == 0:
            return JudgeResult(
                passed=True,
                score=1.0,
                details={
                    "match_type": "structured_output",
                    "field_results": field_results,
                    "missing_fields": missing_fields,
                    "type_mismatches": type_mismatches,
                    "value_mismatches": value_mismatches,
                },
            )

        passed_count = 0
        for field_name, expected_value in fields_spec.items():
            if field_name not in parsed:
                missing_fields.append(field_name)
                field_results[field_name] = {
                    "status": "missing",
                    "expected_value": expected_value,
                }
                continue

            actual_value = parsed[field_name]
            field_passed = True
            entry: dict[str, Any] = {"status": "pass"}

            value_matches = actual_value == expected_value
            if not value_matches:
                value_mismatches.append(field_name)
                entry["status"] = "value_mismatch"
                entry["expected_value"] = expected_value
                entry["actual_value"] = actual_value
                field_passed = False

            if field_name in types_spec:
                type_valid = self._check_type(actual_value, types_spec[field_name])
                if not type_valid:
                    type_mismatches.append(field_name)
                    entry["status"] = "type_mismatch"
                    entry["expected_type"] = types_spec[field_name]
                    entry["actual_type"] = type(actual_value).__name__
                    field_passed = False

            if field_passed:
                passed_count += 1

            field_results[field_name] = entry

        score = round(passed_count / total, 4) if total > 0 else 1.0
        passed = len(missing_fields) == 0 and len(type_mismatches) == 0 and score >= 1.0

        return JudgeResult(
            passed=passed,
            score=score,
            details={
                "match_type": "structured_output",
                "field_results": field_results,
                "missing_fields": missing_fields,
                "type_mismatches": type_mismatches,
                "value_mismatches": value_mismatches,
            },
        )

    @staticmethod
    def _parse_json(text: str) -> tuple[dict[str, Any], str | None]:
        try:
            result = json.loads(text)
        except (json.JSONDecodeError, TypeError) as exc:
            return {}, str(exc)

        if not isinstance(result, dict):
            return {}, f"Expected JSON object, got {type(result).__name__}"

        return result, None

    @staticmethod
    def _check_type(value: Any, expected_type: str) -> bool:
        python_types = _PYTHON_TYPE_MAP.get(expected_type)
        if python_types is None:
            return True
        if expected_type in ("number", "float") and isinstance(value, bool):
            return False
        if expected_type == "int" and isinstance(value, bool):
            return False
        return isinstance(value, python_types)
