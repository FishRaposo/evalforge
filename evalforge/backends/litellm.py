"""LiteLLM backend with offline-first fallback."""

from __future__ import annotations

import os
from typing import Any

from evalforge.backends.base import BackendResponse, BaseBackend
from evalforge.core.clients import LLMClientFactory


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
        self._api_key = (
            api_key or os.getenv("LITELLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        )
        self._model = model
        self._base_url = base_url or os.getenv("LITELLM_BASE_URL")
        self._client: Any | None = None
        self._client_factory = LLMClientFactory()

    async def query(
        self, prompt: str, context: dict[str, Any] | None = None
    ) -> BackendResponse:
        if self._client is None:
            self._client = self._client_factory.create(
                provider="litellm",
                model=self._model,
                api_key=self._api_key,
                base_url=self._base_url,
            )

        client = self._client
        assert client is not None
        completion = await client.complete(
            prompt, context=context, temperature=0.0, max_tokens=1024
        )
        metadata = {
            **completion.metadata,
            "provider": completion.provider,
            "model": completion.model or self._model,
            "usage": completion.usage,
            "tokens_used": completion.usage.get("total_tokens", 0),
            "cache_hit": completion.cache_hit,
            "fallback_path": completion.fallback_path,
        }
        if completion.fallback_path:
            metadata.setdefault("method", "simulated")
        return BackendResponse(
            content=completion.content,
            metadata=metadata,
        )

    async def health_check(self) -> bool:
        return True
