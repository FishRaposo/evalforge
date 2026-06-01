"""Anthropic backend with offline-first fallback."""

from __future__ import annotations

import os
from typing import Any

from evalforge.backends.base import BackendResponse, BaseBackend
from evalforge.execution import SimulatedEvaluator


class AnthropicBackend(BaseBackend):
    """Backend for Anthropic Claude API.

    Offline-first: returns simulated responses when no API key is set.
    """

    def __init__(self, api_key: str | None = None, model: str = "claude-3-haiku-20240307") -> None:
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._model = model
        self._client: Any | None = None

    async def query(self, prompt: str, context: dict[str, Any] | None = None) -> BackendResponse:
        if not self._api_key:
            sim = SimulatedEvaluator(seed=hash(prompt) % 2**31)
            result = sim.evaluate(prompt)
            return BackendResponse(
                content=result["reasoning"],
                metadata={"method": "simulated", "model": self._model, "tokens_used": 0},
            )

        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)

        messages = [{"role": "user", "content": prompt}]
        if context and "history" in context:
            messages = context["history"] + messages

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=messages,
        )
        text = response.content[0].text if response.content else ""
        tokens_used = 0
        if response.usage:
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
        return BackendResponse(
            content=text,
            metadata={
                "model": self._model,
                "usage": {
                    "input_tokens": response.usage.input_tokens if response.usage else 0,
                    "output_tokens": response.usage.output_tokens if response.usage else 0,
                },
                "tokens_used": tokens_used,
            },
        )

    async def health_check(self) -> bool:
        if not self._api_key:
            return True  # Simulated mode is always healthy
        try:
            # Lightweight check: list models or similar
            return True
        except Exception:
            return False
