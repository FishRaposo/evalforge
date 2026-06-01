"""LiteLLM backend with offline-first fallback."""

from __future__ import annotations

import os
from typing import Any

from evalforge.backends.base import BackendResponse, BaseBackend
from evalforge.execution import SimulatedEvaluator


class LiteLLMBackend(BaseBackend):
    """Backend using LiteLLM proxy for unified multi-provider access.

    Offline-first: returns simulated responses when no endpoint is configured.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-3.5-turbo",
        base_url: str | None = None,
    ) -> None:
        self._api_key = api_key or os.getenv("LITELLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self._model = model
        self._base_url = base_url or os.getenv("LITELLM_BASE_URL")
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
            import openai
            self._client = openai.AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)

        messages: list[dict[str, str]] = [{"role": "user", "content": prompt}]
        if context and "history" in context:
            messages = context["history"] + messages

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
        )
        text = response.choices[0].message.content or ""
        usage = response.usage
        tokens_used = 0
        if usage:
            tokens_used = usage.prompt_tokens + usage.completion_tokens
        return BackendResponse(
            content=text,
            metadata={
                "model": self._model,
                "usage": {
                    "input_tokens": usage.prompt_tokens if usage else 0,
                    "output_tokens": usage.completion_tokens if usage else 0,
                },
                "tokens_used": tokens_used,
            },
        )

    async def health_check(self) -> bool:
        return True
