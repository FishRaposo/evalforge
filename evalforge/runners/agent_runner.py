"""Agent test runner for multi-step tool-use evaluation."""

from __future__ import annotations

import json
import time
from typing import Any

from evalforge.backends.base import BaseBackend
from evalforge.judges.base import BaseJudge
from evalforge.judges.exact_match import ExactMatchJudge
from evalforge.judges.registry import _JUDGE_MAP
from evalforge.models.test_case import TestCase, TestCaseType
from evalforge.models.test_result import TestResult
from evalforge.models.trace import AgentTrace, ToolCall, TraceStep
from evalforge.runners.base import BaseRunner


class AgentRunner(BaseRunner):
    """Runner for agent-style multi-step tool-use evaluation."""

    def __init__(self, backend: BaseBackend, max_turns: int = 5) -> None:
        super().__init__(backend)
        self._max_turns = max_turns
        self._judges: dict[TestCaseType, BaseJudge] = {
            tt: judge_cls() for tt, judge_cls in _JUDGE_MAP.items()
        }

    async def run(self, test_case: TestCase) -> TestResult:
        """Execute an agent case and attach an ordered, inspectable trace."""

        start = time.monotonic()
        conversation: list[dict[str, str]] = []
        steps: list[TraceStep] = []
        tool_calls_made: list[dict[str, Any]] = []
        final_response = ""
        backend_metadata: dict[str, Any] = {}
        termination_reason = "completed"

        try:
            for turn_idx in range(self._max_turns):
                turn_start = time.monotonic()
                if turn_idx == 0:
                    conversation.append({"role": "user", "content": test_case.input})
                    prompt = test_case.input
                    context: dict[str, Any] | None = None
                else:
                    prompt = ""
                    context = {"conversation": conversation}

                response = await self._backend.query(prompt, context)
                backend_metadata = response.metadata
                final_response = response.content
                steps.append(
                    TraceStep(
                        turn=turn_idx,
                        index=len(steps),
                        kind="turn",
                        content=response.content,
                        duration_ms=(time.monotonic() - turn_start) * 1000,
                        runtime_metadata={"model": response.metadata.get("model")},
                    )
                )

                parsed_calls = self._parse_tool_calls(response.content)
                tool_calls_made.extend(parsed_calls)
                for raw_call in parsed_calls:
                    call_index = len(
                        [step for step in steps if step.kind == "tool_call"]
                    )
                    error = raw_call.get("_error")
                    call = ToolCall(
                        name=str(raw_call.get("name", "<malformed>")),
                        arguments=self._call_arguments(raw_call),
                        index=call_index,
                        status="error" if error else "parsed",
                        error=str(error) if error else None,
                    )
                    steps.append(
                        TraceStep(
                            turn=turn_idx,
                            index=len(steps),
                            kind="tool_call",
                            tool_call=call,
                            status="error" if error else "ok",
                            error=str(error) if error else None,
                        )
                    )

                if not parsed_calls:
                    break
                conversation.append({"role": "assistant", "content": response.content})
            else:
                termination_reason = "turn_limit"
        except Exception as exc:
            termination_reason = "backend_error"
            steps.append(
                TraceStep(
                    turn=max(0, len(conversation)),
                    index=len(steps),
                    kind="error",
                    status="error",
                    error=str(exc),
                )
            )
            trace = AgentTrace(
                steps=steps,
                final_response=final_response,
                termination_reason=termination_reason,
                tool_call_count=len(
                    [step for step in steps if step.kind == "tool_call"]
                ),
                assertions={"passed": False, "failures": ["backend_error"]},
            )
            elapsed = (time.monotonic() - start) * 1000
            return self._create_result(
                test_case=test_case,
                passed=False,
                score=0.0,
                response=final_response,
                judge_details={"tool_calls": tool_calls_made, "tools_correct": False},
                backend_metadata=backend_metadata,
                agent_trace=trace,
                error=str(exc),
                elapsed_ms=elapsed,
            )

        trace = AgentTrace(
            steps=steps,
            final_response=final_response,
            termination_reason=termination_reason,
            tool_call_count=len([step for step in steps if step.kind == "tool_call"]),
        )
        assertions = self._evaluate_assertions(test_case, tool_calls_made)
        trace.assertions = assertions
        elapsed = (time.monotonic() - start) * 1000
        tools_correct = bool(assertions["passed"])

        if test_case.expected is not None:
            judge = self._judges.get(test_case.type, ExactMatchJudge())
            judge_result = judge.judge(test_case, final_response)
            passed = judge_result.passed and tools_correct
            score = judge_result.score
            details = {
                **judge_result.details,
                "tool_calls": tool_calls_made,
                "tools_correct": tools_correct,
                "trace_assertions": assertions,
            }
        else:
            passed = tools_correct
            score = 1.0 if tools_correct else 0.0
            details = {
                "tool_calls": tool_calls_made,
                "tools_correct": tools_correct,
                "trace_assertions": assertions,
            }

        return self._create_result(
            test_case=test_case,
            passed=passed,
            score=score,
            response=final_response,
            judge_details=details,
            backend_metadata=backend_metadata,
            agent_trace=trace,
            elapsed_ms=elapsed,
        )

    @staticmethod
    def _call_arguments(call: dict[str, Any]) -> dict[str, Any]:
        arguments = call.get("arguments", call.get("args", {}))
        return arguments if isinstance(arguments, dict) else {}

    @staticmethod
    def _evaluate_assertions(
        test_case: TestCase, tool_calls: list[dict[str, Any]]
    ) -> dict[str, Any]:
        names = [str(call.get("name")) for call in tool_calls if call.get("name")]
        failures: list[str] = []
        expected_tools = test_case.metadata.get("expected_tools", [])
        expected_sequence = test_case.metadata.get("expected_tool_sequence", [])
        forbidden = test_case.metadata.get("forbidden_tools", [])
        max_calls = test_case.metadata.get("max_tool_calls")
        expected_tools = (
            [expected_tools]
            if isinstance(expected_tools, str)
            else list(expected_tools or [])
        )
        expected_sequence = (
            [expected_sequence]
            if isinstance(expected_sequence, str)
            else list(expected_sequence or [])
        )
        forbidden = [forbidden] if isinstance(forbidden, str) else list(forbidden or [])
        if any(expected not in names for expected in expected_tools):
            failures.append("expected_tools")
        if expected_sequence and names != [str(item) for item in expected_sequence]:
            failures.append("expected_tool_sequence")
        if max_calls is not None and len(names) > int(max_calls):
            failures.append("max_tool_calls")
        if any(name in forbidden for name in names):
            failures.append("forbidden_tools")
        if any(call.get("_error") for call in tool_calls):
            failures.append("malformed_tool_calls")
        return {
            "passed": not failures,
            "failures": failures,
            "expected_tools": expected_tools,
            "expected_tool_sequence": expected_sequence,
            "forbidden_tools": forbidden,
            "max_tool_calls": max_calls,
            "actual_tools": names,
        }

    def _parse_tool_calls(self, response: str) -> list[dict[str, Any]]:
        """Extract and normalize tool calls, preserving malformed entries."""

        stripped = response.lstrip()
        if not stripped or stripped[0] not in "[{":
            # Plain text is a valid terminal agent response, not a malformed call.
            return []
        try:
            parsed = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            return [
                {
                    "name": "<malformed>",
                    "_error": "invalid JSON tool-call payload",
                }
            ]

        raw_calls: Any = []
        if isinstance(parsed, dict) and "tool_calls" in parsed:
            raw_calls = parsed["tool_calls"]
        elif isinstance(parsed, list):
            raw_calls = [item for item in parsed if isinstance(item, dict)]
        if not isinstance(raw_calls, list):
            return [{"name": "<malformed>", "_error": "tool_calls must be a list"}]

        calls: list[dict[str, Any]] = []
        for item in raw_calls:
            if not isinstance(item, dict) or not item.get("name"):
                calls.append(
                    {"name": "<malformed>", "_error": "tool call must include a name"}
                )
            else:
                calls.append(dict(item))
        return calls
