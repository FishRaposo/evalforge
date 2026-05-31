"""Agent test runner for multi-step tool-use evaluation."""

from __future__ import annotations

import json
import time
from typing import Any

from evalforge.backends.base import BaseBackend
from evalforge.judges.base import BaseJudge
from evalforge.judges.exact_match import ExactMatchJudge
from evalforge.models.test_case import TestCase
from evalforge.models.test_result import TestResult
from evalforge.runners.base import BaseRunner
from evalforge.runners.rag_runner import _JUDGE_MAP


class AgentRunner(BaseRunner):
    """Runner for agent-style multi-step tool-use evaluation.

    Handles test cases that require the AI system to make tool calls
    and validates both the tool selection and the final response.

    Args:
        backend: The AI backend to use for queries.
        max_turns: Maximum number of agent turns before stopping.
    """

    def __init__(self, backend: BaseBackend, max_turns: int = 5) -> None:
        """Initialize the agent runner.

        Args:
            backend: The backend instance for making AI queries.
            max_turns: Maximum agent conversation turns.
        """
        super().__init__(backend)
        self._max_turns = max_turns
        self._judges: dict = {
            tt: judge_cls() for tt, judge_cls in _JUDGE_MAP.items()
        }

    async def run(self, test_case: TestCase) -> TestResult:
        """Execute an agent test case with multi-turn interaction.

        Runs the agent through multiple turns, collecting tool calls
        and validating the final output.

        Args:
            test_case: The test case to execute.

        Returns:
            The evaluation result including tool call validation.
        """
        start = time.monotonic()
        conversation: list[dict[str, str]] = []

        try:
            final_response = ""
            tool_calls_made: list[dict[str, Any]] = []

            for turn_idx in range(self._max_turns):
                if turn_idx == 0:
                    conversation.append(
                        {"role": "user", "content": test_case.input}
                    )
                    prompt = test_case.input
                    context: dict[str, Any] | None = None
                else:
                    prompt = ""
                    context = {"conversation": conversation}

                response = await self._backend.query(prompt, context)
                final_response = response.content

                parsed_calls = self._parse_tool_calls(response.content)
                tool_calls_made.extend(parsed_calls)

                if not parsed_calls:
                    break

                conversation.append(
                    {"role": "assistant", "content": response.content}
                )

        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return self._create_result(
                test_case=test_case,
                passed=False,
                score=0.0,
                response="",
                error=str(exc),
                elapsed_ms=elapsed,
            )

        elapsed = (time.monotonic() - start) * 1000

        expected_tools = test_case.metadata.get("expected_tools", [])
        tools_correct = all(
            any(t.get("name") == exp for t in tool_calls_made)
            for exp in expected_tools
        )

        if test_case.expected is not None:
            judge = self._judges.get(test_case.type, ExactMatchJudge())
            judge_result = judge.judge(test_case, final_response)
            passed = judge_result.passed and tools_correct
            score = judge_result.score
            details = {
                **judge_result.details,
                "tool_calls": tool_calls_made,
                "tools_correct": tools_correct,
            }
        else:
            passed = tools_correct
            score = 1.0 if tools_correct else 0.0
            details = {"tool_calls": tool_calls_made, "tools_correct": tools_correct}

        return self._create_result(
            test_case=test_case,
            passed=passed,
            score=score,
            response=final_response,
            judge_details=details,
            elapsed_ms=elapsed,
        )

    def _parse_tool_calls(self, response: str) -> list[dict[str, Any]]:
        """Extract tool call information from an agent response.

        Attempts to parse JSON-formatted tool calls from the response.

        Args:
            response: The raw agent response text.

        Returns:
            A list of parsed tool call dictionaries.
        """
        tool_calls: list[dict[str, Any]] = []

        try:
            parsed = json.loads(response)
            if isinstance(parsed, dict) and "tool_calls" in parsed:
                tool_calls.extend(parsed["tool_calls"])
            elif isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and "name" in item:
                        tool_calls.append(item)
        except (json.JSONDecodeError, TypeError):
            pass

        return tool_calls
