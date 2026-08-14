"""Formal agent trace and tool assertion contracts."""

from __future__ import annotations

import pytest

from evalforge.backends.base import BackendResponse, BaseBackend
from evalforge.models.test_case import TestCase, TestCaseType
from evalforge.runners.agent_runner import AgentRunner


class SequenceBackend(BaseBackend):
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.index = 0

    async def query(self, prompt: str, context=None) -> BackendResponse:
        value = self.responses[min(self.index, len(self.responses) - 1)]
        self.index += 1
        return BackendResponse(content=value, metadata={"model": "fixture"})

    async def health_check(self) -> bool:
        return True


class FailingBackend(BaseBackend):
    async def query(self, prompt: str, context=None) -> BackendResponse:
        raise RuntimeError("fixture backend failed")

    async def health_check(self) -> bool:
        return False


def _case(**metadata) -> TestCase:
    return TestCase(
        id="trace-case",
        name="Trace case",
        type=TestCaseType.EXACT_ANSWER,
        input="calculate",
        expected="done",
        metadata=metadata,
    )


@pytest.mark.asyncio
async def test_agent_runner_records_turns_and_tool_calls() -> None:
    backend = SequenceBackend(
        [
            '{"tool_calls": [{"name": "calculator", "args": {"x": 2}}]}',
            "done",
        ]
    )

    result = await AgentRunner(backend).run(
        _case(expected_tools=["calculator"], expected_tool_sequence=["calculator"])
    )

    assert result.passed is True
    assert result.agent_trace is not None
    assert result.agent_trace.tool_call_count == 1
    assert any(step.kind == "tool_call" for step in result.agent_trace.steps)
    assert result.agent_trace.assertions["passed"] is True
    assert result.judge_details["tool_calls"][0]["name"] == "calculator"


@pytest.mark.asyncio
async def test_trace_assertions_report_missing_wrong_forbidden_and_max_calls() -> None:
    backend = SequenceBackend(
        [
            '{"tool_calls": [{"name": "search", "args": {}}]}',
            '{"tool_calls": [{"name": "calculator", "args": {}}]}',
            "done",
        ]
    )

    result = await AgentRunner(backend, max_turns=3).run(
        _case(
            expected_tools=["calculator"],
            expected_tool_sequence=["calculator", "search"],
            forbidden_tools=["search"],
            max_tool_calls=1,
        )
    )

    assert result.passed is False
    assert result.agent_trace is not None
    assert result.agent_trace.assertions["passed"] is False
    assert set(result.agent_trace.assertions["failures"]) >= {
        "expected_tool_sequence",
        "forbidden_tools",
        "max_tool_calls",
    }


@pytest.mark.asyncio
async def test_malformed_tool_call_is_recorded_as_trace_error() -> None:
    result = await AgentRunner(
        SequenceBackend(['{"tool_calls": ["bad"]}', "done"])
    ).run(_case())

    assert result.agent_trace is not None
    assert result.agent_trace.termination_reason == "completed"
    assert any(step.status == "error" for step in result.agent_trace.steps)


@pytest.mark.asyncio
async def test_malformed_json_tool_payload_is_recorded_as_trace_error() -> None:
    result = await AgentRunner(SequenceBackend(['{"tool_calls": [', "done"])).run(
        _case()
    )

    assert result.agent_trace is not None
    assert any(
        step.error == "invalid JSON tool-call payload"
        for step in result.agent_trace.steps
    )
    assert result.agent_trace.assertions["passed"] is False


@pytest.mark.asyncio
async def test_backend_error_preserves_partial_trace() -> None:
    result = await AgentRunner(FailingBackend()).run(_case())

    assert result.passed is False
    assert result.error == "fixture backend failed"
    assert result.agent_trace is not None
    assert result.agent_trace.termination_reason == "backend_error"
    assert result.agent_trace.steps[-1].kind == "error"


@pytest.mark.asyncio
async def test_turn_limit_is_explicit_in_trace() -> None:
    result = await AgentRunner(
        SequenceBackend(['{"tool_calls": [{"name": "search"}]}']), max_turns=2
    ).run(_case(expected_tools=["search"]))

    assert result.agent_trace is not None
    assert result.agent_trace.termination_reason == "turn_limit"
