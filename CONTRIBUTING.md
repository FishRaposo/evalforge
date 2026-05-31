# Contributing to EvalForge

Thank you for your interest in contributing to EvalForge! This guide covers everything you need to get started.

## Development Setup

### Prerequisites

- Python 3.11 or later
- pip (latest version recommended)
- Git

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/evalforge.git
cd evalforge

# Install with dev dependencies
pip install -e ".[dev]"

# Or use the Makefile
make setup
```

This installs EvalForge in editable mode along with `pytest`, `pytest-asyncio`, `ruff`, and `mypy`.

### Verify Installation

```bash
make test
```

All tests should pass. If they don't, open an issue.

## Architecture Overview

EvalForge follows a pipeline architecture with these components:

```
CLI (Typer) -> Suite Loader (YAML) -> Runner -> Backend -> Judge -> Reporter
```

| Component    | Location                  | Responsibility                                        |
|-------------|---------------------------|-------------------------------------------------------|
| CLI         | `evalforge/cli.py`        | Parse commands, wire components together              |
| Loader      | `evalforge/loader/`       | Parse and validate YAML test suites                   |
| Runner      | `evalforge/runners/`      | Orchestrate test execution against backends           |
| Backend     | `evalforge/backends/`     | Query AI systems (mock, OpenAI-compatible, cached)    |
| Judge       | `evalforge/judges/`       | Evaluate responses against expected behavior          |
| Reporter    | `evalforge/reporters/`    | Generate output reports (Markdown, JSON, HTML)        |
| Models      | `evalforge/models/`       | Pydantic data models shared across all components     |

### Data Flow

1. The CLI receives a suite YAML path and options.
2. The `SuiteLoader` parses the YAML into a `TestSuite` model.
3. A `Runner` (RAG or Agent) iterates over `TestCase` objects.
4. For each case, the runner calls a `Backend` to get a response.
5. The response is passed to the appropriate `Judge` for evaluation.
6. Results are collected into a `Report` and rendered by a `Reporter`.

## Code Style

EvalForge uses **ruff** for linting and formatting, and **mypy** in strict mode for type checking.

### Key Rules

- **Line length**: 100 characters max
- **Python version**: 3.11+ (use `from __future__ import annotations` in all files)
- **Type hints**: Required on all function signatures (mypy `strict` enforces this)
- **No inline comments**: Code should be self-documenting; use docstrings for public APIs
- **Imports**: Sorted automatically by ruff (isort-compatible)
- **Strings**: Prefer double quotes (ruff default)

### Running Checks

```bash
# Lint
make lint

# Format
make format

# Type check only
mypy evalforge
```

### Pre-commit Hooks

We recommend installing pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

This runs ruff, mypy, and basic file checks before each commit.

## Testing

EvalForge uses **pytest** with **pytest-asyncio** for async tests.

### Running Tests

```bash
# Full suite with coverage
make test

# Specific test file
python -m pytest tests/test_judges.py -v

# Specific test class
python -m pytest tests/test_judges.py::TestExactMatchJudge -v
```

### Coverage Target

We aim for **80%+ code coverage**. Coverage reports are printed after each test run via `--cov-report=term-missing`.

### Writing Tests

Follow the patterns in `tests/`:

```python
"""Tests for <component>."""

from __future__ import annotations

import pytest

from evalforge.judges.base import BaseJudge, JudgeResult
from evalforge.models.test_case import TestCase, TestCaseType


class TestMyJudge:
    """Tests for MyJudge."""

    def test_something(self) -> None:
        judge = MyJudge()
        test_case = TestCase(
            id="test-id",
            name="Test name",
            type=TestCaseType.EXACT_ANSWER,
            input="Input",
            expected="Expected",
        )
        result = judge.judge(test_case, "Response")
        assert result.passed is True
```

### Key Conventions

- Use `from __future__ import annotations` in all test files.
- Group tests by class per component (e.g., `TestExactMatchJudge`).
- Use descriptive method names: `test_<behavior>_<condition>`.
- Use fixtures from `conftest.py` when applicable.
- Mark async tests with `@pytest.mark.asyncio`.

## Adding New Judges

Judges evaluate AI responses and return a `JudgeResult`. To add a new judge:

### Step 1: Create the Judge

Create a new file in `evalforge/judges/` (e.g., `my_judge.py`):

```python
"""Judge for <description>."""

from __future__ import annotations

from evalforge.judges.base import BaseJudge, JudgeResult
from evalforge.models.test_case import TestCase


class MyJudge(BaseJudge):
    """Evaluates <what it checks>."""

    def judge(self, test_case: TestCase, response: str) -> JudgeResult:
        expected = test_case.expected
        passed = False
        score = 0.0
        details: dict[str, Any] = {}

        # ... evaluation logic ...

        return JudgeResult(passed=passed, score=score, details=details)
```

### Step 2: Add Test Case Type

If needed, add a new enum value to `TestCaseType` in `evalforge/models/test_case.py`.

### Step 3: Register the Judge

Update the judge dispatch logic in the runner or CLI to map your `TestCaseType` to your new judge.

### Step 4: Write Tests

Create tests in `tests/test_judges.py` following the existing class pattern:

```python
class TestMyJudge:
    def test_pass_condition(self) -> None:
        ...

    def test_fail_condition(self) -> None:
        ...
```

### Step 5: Add Example Suite

Create a YAML file in `example_suites/` demonstrating the new judge.

## Adding New Backends

Backends query AI systems and return `BackendResponse` objects.

### Step 1: Create the Backend

Create a new file in `evalforge/backends/`:

```python
"""Backend for <system>."""

from __future__ import annotations

from typing import Any, Optional

from evalforge.backends.base import BackendResponse, BaseBackend


class MyBackend(BaseBackend):
    """Backend that queries <system>."""

    async def query(
        self, prompt: str, context: Optional[dict[str, Any]] = None
    ) -> BackendResponse:
        # ... implementation ...
        return BackendResponse(content="...", metadata={...})

    async def health_check(self) -> bool:
        # ... implementation ...
        return True
```

### Step 2: Wire Into CLI

Update `evalforge/cli.py` to accept the new backend name via `--backend`.

### Step 3: Write Tests

Test against the mock backend pattern. Use `MockBackend` as a reference for how tests should be structured.

## Adding New Reporters

Reporters take a `Report` and generate output files.

### Step 1: Create the Reporter

Create a new file in `evalforge/reporters/`:

```python
"""Reporter for <format>."""

from __future__ import annotations

from pathlib import Path

from evalforge.models.report import Report


class MyReporter:
    """Generates <format> reports."""

    def generate(self, report: Report, output_dir: Path) -> Path:
        # ... generate output ...
        return output_path
```

### Step 2: Wire Into CLI

Add the format option to the `--format` flag in `evalforge/cli.py`.

### Step 3: Write Tests

Follow the pattern in `tests/test_reporters.py`:

```python
class TestMyReporter:
    def test_report_generation(self, sample_report: Report, temp_output_dir: Path) -> None:
        reporter = MyReporter()
        output_path = reporter.generate(sample_report, temp_output_dir)
        assert output_path.exists()
```

## Creating Test Suites

Test suites are YAML files that define evaluation scenarios.

### Suite Structure

```yaml
name: "My Evaluation Suite"
description: "Tests for my RAG system"
version: "1.0"

test_cases:
  - id: "tc-001"
    name: "Factual accuracy"
    type: exact_answer
    input: "What is the capital of France?"
    expected: "Paris"
    tags: [facts, geography]

  - id: "tc-002"
    name: "Source citation"
    type: must_cite
    input: "Tell me about climate change"
    expected:
      sources:
        - "IPCC AR6 Report"
    tags: [citations, climate]
```

### Supported Test Types

| Type                 | Judge                  | Expected Format                     |
|---------------------|------------------------|-------------------------------------|
| `exact_answer`      | `ExactMatchJudge`      | String                              |
| `semantic_answer`   | `SemanticMatchJudge`   | String                              |
| `must_cite`         | `CitationCheckJudge`   | `{"sources": [...]}`               |
| `must_refuse`       | `RefusalCheckJudge`    | `null`                              |
| `must_retrieve`     | `RetrievalCheckJudge`  | `{"documents": [...]}`             |
| `forbidden_content` | `ForbiddenContentJudge`| `{"forbidden": [...]}`             |
| `structured_output` | `StructuredOutputJudge`| `{"fields": {...}, "types": {...}}`|

### Includes

Suites can include other suites:

```yaml
name: "Extended Suite"
includes:
  - "base_suite.yaml"
test_cases:
  - id: "ext-001"
    ...
```

## PR Process

1. **Fork and branch**: Create a feature branch from `main`.
2. **Write code**: Follow the style guide above.
3. **Write tests**: All new code needs test coverage.
4. **Run checks**: `make lint && make test` must pass.
5. **Commit**: Use clear, descriptive commit messages.
6. **Open PR**: Fill out the PR template with motivation and testing details.
7. **Review**: Address review feedback. CI must pass before merge.

### CI Checks

Every PR runs:
- `ruff check` and `ruff format --check`
- `mypy evalforge` (strict mode)
- `pytest --cov=evalforge` (coverage gate at 80%)

### Commit Messages

Use the imperative mood:

```
Add StructuredOutputJudge for JSON response validation
Fix cache eviction ordering in CachingBackend
Update CONTRIBUTING.md with judge extension guide
```

## Getting Help

- Open a GitHub issue for bugs or feature requests.
- Start a discussion for questions or design proposals.

Thank you for contributing to EvalForge!
