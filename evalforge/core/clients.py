"""Provider-neutral LLM clients with deterministic offline fallback."""

from __future__ import annotations

import hashlib
import os
from typing import Any, Mapping

from evalforge.core.contracts import Completion, LLMClient
from evalforge.execution import SimulatedEvaluator


def _stable_seed(prompt: str) -> int:
    return int.from_bytes(hashlib.sha256(prompt.encode()).digest()[:8], "big") % (2**31)


class OfflineLLMClient:
    """Credential-free deterministic client used by default and in CI."""

    def __init__(self, model: str = "mock", provider: str = "offline") -> None:
        self.model = model
        self.provider = provider

    async def complete(
        self,
        prompt: str,
        *,
        context: Mapping[str, Any] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> Completion:
        result = SimulatedEvaluator(seed=_stable_seed(prompt)).evaluate(prompt)
        return Completion(
            content=str(result.get("reasoning", "")),
            provider=self.provider,
            model=self.model,
            fallback_path="offline-simulated",
            metadata={
                "method": "simulated",
                "score": result.get("score", 0.0),
                "fallback_path": "offline-simulated",
            },
        )


class OpenAICompatibleClient:
    """OpenAI-compatible adapter with lazy optional dependency loading."""

    def __init__(
        self,
        *,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url
        self._client = client

    async def complete(
        self,
        prompt: str,
        *,
        context: Mapping[str, Any] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> Completion:
        if self._client is None:
            if not self.api_key:
                return await OfflineLLMClient(self.model, "openai").complete(
                    prompt,
                    context=context,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            import openai

            self._client = openai.AsyncOpenAI(
                api_key=self.api_key, base_url=self.base_url
            )
        messages: list[Any] = []
        if context and isinstance(context.get("system"), str):
            messages.append({"role": "system", "content": context["system"]})
        if context and isinstance(context.get("conversation"), list):
            messages.extend(context["conversation"])
        if context and isinstance(context.get("messages"), list):
            messages.extend(context["messages"])
        messages.append({"role": "user", "content": prompt})
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        message = response.choices[0].message
        usage = getattr(response, "usage", None)
        usage_data = {
            "prompt_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
            "completion_tokens": int(getattr(usage, "completion_tokens", 0) or 0),
        }
        usage_data["total_tokens"] = (
            usage_data["prompt_tokens"] + usage_data["completion_tokens"]
        )
        return Completion(
            content=getattr(message, "content", "") or "",
            provider="openai",
            model=getattr(response, "model", self.model),
            usage=usage_data,
            metadata={"provider": "openai"},
        )


class AnthropicClient:
    """Anthropic adapter with the same completion contract."""

    def __init__(
        self,
        *,
        model: str = "claude-3-haiku-20240307",
        api_key: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._client = client

    async def complete(
        self,
        prompt: str,
        *,
        context: Mapping[str, Any] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> Completion:
        if self._client is None:
            if not self.api_key:
                return await OfflineLLMClient(self.model, "anthropic").complete(
                    prompt,
                    context=context,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            import anthropic

            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
        response = await self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        usage = getattr(response, "usage", None)
        usage_data = {
            "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        }
        usage_data["total_tokens"] = (
            usage_data["input_tokens"] + usage_data["output_tokens"]
        )
        content_block: Any = response.content[0] if response.content else None
        content = str(getattr(content_block, "text", "") or "")
        return Completion(
            content=content,
            provider="anthropic",
            model=self.model,
            usage=usage_data,
            metadata={"provider": "anthropic"},
        )


class LiteLLMClient:
    """Optional LiteLLM adapter; import remains lazy and non-required."""

    def __init__(self, *, model: str, api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("LITELLM_API_KEY")

    async def complete(
        self,
        prompt: str,
        *,
        context: Mapping[str, Any] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> Completion:
        try:
            import litellm
        except ImportError:
            return await OfflineLLMClient(self.model, "litellm").complete(
                prompt, context=context, temperature=temperature, max_tokens=max_tokens
            )
        response = await litellm.acompletion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            api_key=self.api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        message = response["choices"][0]["message"]
        usage = response.get("usage", {})
        return Completion(
            content=message.get("content", "") or "",
            provider="litellm",
            model=response.get("model", self.model),
            usage={
                key: int(value)
                for key, value in usage.items()
                if isinstance(value, int)
            },
            metadata={"provider": "litellm"},
        )


class LLMClientFactory:
    """Create provider clients without making a provider dependency mandatory."""

    def create(
        self,
        *,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
        client: Any | None = None,
    ) -> LLMClient:
        if client is not None and hasattr(client, "complete"):
            return client
        normalized = provider.lower().replace("-", "_")
        if normalized in {"anthropic", "claude"}:
            return AnthropicClient(model=model, api_key=api_key, client=client)
        if normalized in {"litellm", "lite_llm"}:
            return LiteLLMClient(model=model, api_key=api_key)
        return OpenAICompatibleClient(
            model=model, api_key=api_key, base_url=base_url, client=client
        )

    create_client = create
