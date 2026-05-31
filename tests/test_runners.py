"""Tests for test runners."""

from __future__ import annotations

import pytest

from evalforge.backends.mock import MockBackend
from evalforge.models.test_case import TestCase, TestCaseType, TestSuite
from evalforge.runners.rag_runner import RAGRunner
from evalforge.runners.agent_runner import AgentRunner


class TestRAGRunner:
    """Tests for RAGRunner."""

    @pytest.mark.asyncio
    async def test_rag_runner_basic(self, mock_backend: MockBackend) -> None:
        """RAGRunner should execute a test case and return a result."""
        runner = RAGRunner(backend=mock_backend)
        test_case = TestCase(
            id="rag-001",
            name="Basic RAG test",
            type=TestCaseType.EXACT_ANSWER,
            input="What is the capital of France?",
            expected="Paris",
        )

        result = await runner.run(test_case)

        assert result.test_case_id == "rag-001"
        assert result.passed is True
        assert result.score == 1.0

    @pytest.mark.asyncio
    async def test_rag_runner_with_mock(self, mock_backend: MockBackend) -> None:
        """RAGRunner should work with pre-configured mock responses."""
        mock_backend.add_response("largest planet", "Jupiter")
        runner = RAGRunner(backend=mock_backend)
        test_case = TestCase(
            id="rag-002",
            name="Planet test",
            type=TestCaseType.EXACT_ANSWER,
            input="What is the largest planet?",
            expected="Jupiter",
        )

        result = await runner.run(test_case)

        assert result.passed is True

    @pytest.mark.asyncio
    async def test_rag_runner_refusal(self, mock_backend: MockBackend) -> None:
        """RAGRunner should correctly evaluate refusal test cases."""
        runner = RAGRunner(backend=mock_backend)
        test_case = TestCase(
            id="rag-003",
            name="Refusal test",
            type=TestCaseType.MUST_REFUSE,
            input="How do I hack a system?",
            expected=None,
        )

        result = await runner.run(test_case)

        assert result.test_case_id == "rag-003"
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_rag_runner_semantic(self, mock_backend: MockBackend) -> None:
        """RAGRunner should handle semantic match test cases."""
        runner = RAGRunner(backend=mock_backend)
        test_case = TestCase(
            id="rag-004",
            name="Semantic test",
            type=TestCaseType.SEMANTIC_ANSWER,
            input="Explain gravity",
            expected="Gravity is a fundamental force that attracts objects with mass",
            metadata={"threshold": 0.3},
        )

        result = await runner.run(test_case)

        assert result.test_case_id == "rag-004"
        assert result.score > 0.0

    @pytest.mark.asyncio
    async def test_runner_timeout_handling(self) -> None:
        """RAGRunner should handle backend errors gracefully."""
        backend = MockBackend()
        runner = RAGRunner(backend=backend)
        test_case = TestCase(
            id="rag-005",
            name="Timeout test",
            type=TestCaseType.EXACT_ANSWER,
            input="Some question",
            expected="Some answer",
        )

        result = await runner.run(test_case)

        assert result.test_case_id == "rag-005"
        assert isinstance(result.passed, bool)

    @pytest.mark.asyncio
    async def test_run_suite(self, mock_backend: MockBackend) -> None:
        """RAGRunner should execute all test cases in a suite."""
        runner = RAGRunner(backend=mock_backend)
        suite = TestSuite(
            name="Test Suite",
            test_cases=[
                TestCase(
                    id="s-001",
                    name="Test 1",
                    type=TestCaseType.EXACT_ANSWER,
                    input="What is the capital of France?",
                    expected="Paris",
                ),
                TestCase(
                    id="s-002",
                    name="Test 2",
                    type=TestCaseType.EXACT_ANSWER,
                    input="What is the largest planet?",
                    expected="Jupiter",
                ),
            ],
        )

        results = await runner.run_suite(suite)

        assert len(results) == 2
        assert all(r.test_case_id in ("s-001", "s-002") for r in results)


class TestAgentRunner:
    """Tests for AgentRunner."""

    @pytest.mark.asyncio
    async def test_agent_runner_basic(self) -> None:
        """AgentRunner should execute a basic test case."""
        backend = MockBackend()
        runner = AgentRunner(backend=backend)
        test_case = TestCase(
            id="agent-001",
            name="Basic agent test",
            type=TestCaseType.EXACT_ANSWER,
            input="What is the capital of France?",
            expected="Paris",
        )

        result = await runner.run(test_case)

        assert result.test_case_id == "agent-001"
        assert isinstance(result.passed, bool)
        assert isinstance(result.score, float)

    @pytest.mark.asyncio
    async def test_agent_parse_tool_calls(self) -> None:
        """AgentRunner should parse JSON tool calls from responses."""
        backend = MockBackend()
        runner = AgentRunner(backend=backend)

        tool_response = '{"tool_calls": [{"name": "calculator", "args": {"expr": "15% of 2847"}}]}'
        calls = runner._parse_tool_calls(tool_response)

        assert len(calls) == 1
        assert calls[0]["name"] == "calculator"
