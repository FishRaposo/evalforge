"""YAML test suite loader with validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from evalforge.loader.schema import SuiteFile, TestCaseFile
from evalforge.models.test_case import TestCase, TestSuite


class SuiteLoader:
    """Loads and validates YAML test suite files into TestSuite models.

    Provides methods to parse YAML files, validate their structure against
    the expected schema, and convert them into Pydantic TestSuite models.
    """

    def load_suite(self, path: Path) -> TestSuite:
        """Load a test suite from a YAML file.

        Args:
            path: Path to the YAML test suite file.

        Returns:
            A validated TestSuite instance.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the YAML is invalid or schema validation fails.
        """
        if not Path(path).exists():
            raise FileNotFoundError(f"Suite file not found: {path}")

        raw_data = self._parse_yaml(Path(path))
        raw_data = self._resolve_includes(raw_data, Path(path).parent)

        try:
            suite_file = SuiteFile.model_validate(raw_data)
        except ValidationError as exc:
            raise ValueError(f"Schema validation failed for {path}: {exc}") from exc

        test_cases = [
            TestCase(
                id=tc.id,
                name=tc.name,
                type=tc.type,
                input=tc.input,
                expected=tc.expected,
                metadata=tc.metadata,
                tags=tc.tags,
            )
            for tc in suite_file.test_cases
        ]

        return TestSuite(
            name=suite_file.name,
            description=suite_file.description,
            version=suite_file.version,
            backend=suite_file.backend,
            test_cases=test_cases,
        )

    def validate_suite(self, suite: TestSuite) -> list[str]:
        """Validate a loaded test suite for correctness.

        Checks for common issues like duplicate IDs, missing expected
        values for types that require them, and empty suites.

        Args:
            suite: The TestSuite to validate.

        Returns:
            A list of validation error strings. Empty list means valid.
        """
        errors: list[str] = []

        if not suite.test_cases:
            errors.append("Suite contains no test cases")
            return errors

        seen_ids: set[str] = set()
        for tc in suite.test_cases:
            if tc.id in seen_ids:
                errors.append(f"Duplicate test case ID: {tc.id}")
            seen_ids.add(tc.id)

            types_requiring_expected = {
                "exact_answer", "semantic_answer", "must_cite",
                "must_retrieve", "forbidden_content", "structured_output",
            }
            if tc.type.value in types_requiring_expected and tc.expected is None:
                errors.append(
                    f"Test case '{tc.id}' of type '{tc.type.value}' requires an expected value"
                )

        return errors

    def _parse_yaml(self, path: Path) -> dict[str, Any]:
        """Parse a YAML file into a dictionary.

        Args:
            path: Path to the YAML file.

        Returns:
            Parsed YAML data as a dictionary.

        Raises:
            ValueError: If the file contains invalid YAML syntax.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(f"Expected YAML mapping at top level in {path}")

        return data

    def _resolve_includes(
        self, data: dict[str, Any], base_dir: Path
    ) -> dict[str, Any]:
        """Resolve include directives in the suite data.

        If the data contains an 'includes' key with a list of file paths,
        loads each file and merges its test_cases into the main data.

        Args:
            data: The parsed YAML data.
            base_dir: Directory of the main suite file for resolving relative paths.

        Returns:
            The data with includes resolved.
        """
        includes = data.pop("includes", [])
        if not includes:
            return data

        merged_cases: list[dict[str, Any]] = list(data.get("test_cases", []))

        for include_path in includes:
            include_file = base_dir / include_path
            if not include_file.exists():
                continue

            included_data = self._parse_yaml(include_file)
            if "test_cases" in included_data:
                merged_cases.extend(included_data["test_cases"])

        data["test_cases"] = merged_cases
        return data
