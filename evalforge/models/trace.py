"""Portable, inspectable traces for agent evaluations."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A normalized tool invocation observed in an agent response."""

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    index: int = Field(default=0, ge=0)
    status: Literal["parsed", "error"] = "parsed"
    error: str | None = None


class TraceStep(BaseModel):
    """One ordered turn, tool call, or trace error."""

    turn: int = Field(ge=0)
    index: int = Field(ge=0)
    kind: Literal["turn", "tool_call", "error"]
    content: str = ""
    tool_call: ToolCall | None = None
    status: Literal["ok", "error"] = "ok"
    error: str | None = None
    duration_ms: float = Field(default=0.0, ge=0.0)
    runtime_metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def step_kind(self) -> str:
        """Compatibility alias for consumers using ``step_kind``."""

        return self.kind


class AgentTrace(BaseModel):
    """Complete ordered agent trace attached to a test result."""

    steps: list[TraceStep] = Field(default_factory=list)
    final_response: str = ""
    termination_reason: str = "completed"
    tool_call_count: int = Field(default=0, ge=0)
    assertions: dict[str, Any] = Field(default_factory=dict)

    @property
    def tool_calls(self) -> list[ToolCall]:
        return [
            step.tool_call
            for step in self.steps
            if step.kind == "tool_call" and step.tool_call is not None
        ]
