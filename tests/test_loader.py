"""Tests for the suite loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from evalforge.loader.suite_loader import SuiteLoader
from evalforge.models.test_case import TestCaseType


class TestSuiteLoader:
    """Tests for SuiteLoader YAML parsing and validation."""

    def test_load_valid_suite(self, tmp_path: Path) -> None:
        """SuiteLoader should parse a valid YAML suite file."""
        suite_yaml = """
name: "Test Suite"
description: "A valid test suite"
version: "1.0"

test_cases:
  - id: "tc-001"
    name: "Capital question"
    type: exact_answer
    input: "What is the capital of France?"
    expected: "Paris"
    tags: [facts]
"""
        suite_file = tmp_path / "valid_suite.yaml"
        suite_file.write_text(suite_yaml, encoding="utf-8")

        loader = SuiteLoader()
        suite = loader.load_suite(suite_file)

        assert suite.name == "Test Suite"
        assert suite.description == "A valid test suite"
        assert len(suite.test_cases) == 1
        assert suite.test_cases[0].id == "tc-001"
        assert suite.test_cases[0].type == TestCaseType.EXACT_ANSWER
        assert suite.test_cases[0].expected == "Paris"

    def test_load_invalid_yaml(self, tmp_path: Path) -> None:
        """SuiteLoader should raise ValueError for malformed YAML."""
        suite_file = tmp_path / "invalid.yaml"
        suite_file.write_text(":\n  invalid: yaml: content:\n  - [", encoding="utf-8")

        loader = SuiteLoader()

        with pytest.raises(ValueError, match="Invalid YAML"):
            loader.load_suite(suite_file)

    def test_validate_suite_errors(self) -> None:
        """validate_suite should return errors for invalid suites."""
        from evalforge.models.test_case import TestCase, TestSuite

        suite = TestSuite(
            name="Empty Suite",
            test_cases=[],
        )

        loader = SuiteLoader()
        errors = loader.validate_suite(suite)

        assert len(errors) > 0
        assert any("no test cases" in e.lower() for e in errors)

    def test_validate_duplicate_ids(self) -> None:
        """validate_suite should detect duplicate test case IDs."""
        from evalforge.models.test_case import TestCase, TestSuite

        suite = TestSuite(
            name="Duplicate Suite",
            test_cases=[
                TestCase(
                    id="dup-001",
                    name="First",
                    type=TestCaseType.EXACT_ANSWER,
                    input="Q1",
                    expected="A1",
                ),
                TestCase(
                    id="dup-001",
                    name="Second",
                    type=TestCaseType.EXACT_ANSWER,
                    input="Q2",
                    expected="A2",
                ),
            ],
        )

        loader = SuiteLoader()
        errors = loader.validate_suite(suite)

        assert any("Duplicate" in e for e in errors)

    def test_resolve_includes(self, tmp_path: Path) -> None:
        """SuiteLoader should resolve include directives."""
        included_yaml = """
test_cases:
  - id: "inc-001"
    name: "Included test"
    type: exact_answer
    input: "Question"
    expected: "Answer"
"""
        included_file = tmp_path / "included.yaml"
        included_file.write_text(included_yaml, encoding="utf-8")

        main_yaml = f"""
name: "Main Suite"
description: "Suite with includes"
version: "1.0"
includes:
  - "included.yaml"
test_cases:
  - id: "main-001"
    name: "Main test"
    type: exact_answer
    input: "Main question"
    expected: "Main answer"
"""
        main_file = tmp_path / "main.yaml"
        main_file.write_text(main_yaml, encoding="utf-8")

        loader = SuiteLoader()
        suite = loader.load_suite(main_file)

        assert len(suite.test_cases) == 2
        assert suite.test_cases[0].id == "main-001"
        assert suite.test_cases[1].id == "inc-001"

    def test_missing_expected_for_required_type(self, tmp_path: Path) -> None:
        """validate_suite should flag missing expected for types that require it."""
        from evalforge.models.test_case import TestCase, TestSuite

        suite = TestSuite(
            name="Missing Expected",
            test_cases=[
                TestCase(
                    id="no-exp",
                    name="No expected value",
                    type=TestCaseType.EXACT_ANSWER,
                    input="Question",
                    expected=None,
                ),
            ],
        )

        loader = SuiteLoader()
        errors = loader.validate_suite(suite)

        assert any("requires an expected value" in e for e in errors)

    def test_file_not_found(self) -> None:
        """SuiteLoader should raise FileNotFoundError for missing files."""
        loader = SuiteLoader()

        with pytest.raises(FileNotFoundError):
            loader.load_suite(Path("/nonexistent/suite.yaml"))
