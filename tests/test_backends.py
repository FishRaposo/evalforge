"""Tests for Anthropic, HuggingFace, and LiteLLM backends."""

from __future__ import annotations

import pytest

from evalforge.backends.anthropic import AnthropicBackend
from evalforge.backends.huggingface import HuggingFaceBackend
from evalforge.backends.litellm import LiteLLMBackend


class TestAnthropicBackend:
    """Tests for AnthropicBackend."""

    @pytest.mark.asyncio
    async def test_simulated_query(self) -> None:
        backend = AnthropicBackend(api_key=None, model="claude-3-haiku-20240307")
        response = await backend.query("Tell me a story")
        assert response.content != ""
        assert response.metadata["method"] == "simulated"
        assert response.metadata["model"] == "claude-3-haiku-20240307"

    @pytest.mark.asyncio
    async def test_health_check(self) -> None:
        backend = AnthropicBackend(api_key=None)
        assert await backend.health_check() is True


class TestHuggingFaceBackend:
    """Tests for HuggingFaceBackend."""

    @pytest.mark.asyncio
    async def test_simulated_query(self) -> None:
        backend = HuggingFaceBackend(api_token=None, model="meta-llama/Llama-2-7b-chat-hf")
        response = await backend.query("Tell me a story")
        assert response.content != ""
        assert response.metadata["method"] == "simulated"
        assert response.metadata["model"] == "meta-llama/Llama-2-7b-chat-hf"

    @pytest.mark.asyncio
    async def test_health_check(self) -> None:
        backend = HuggingFaceBackend(api_token=None)
        assert await backend.health_check() is True


class TestLiteLLMBackend:
    """Tests for LiteLLMBackend."""

    @pytest.mark.asyncio
    async def test_simulated_query(self) -> None:
        backend = LiteLLMBackend(api_key=None, model="gpt-3.5-turbo")
        response = await backend.query("Tell me a story")
        assert response.content != ""
        assert response.metadata["method"] == "simulated"
        assert response.metadata["model"] == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_health_check(self) -> None:
        backend = LiteLLMBackend(api_key=None)
        assert await backend.health_check() is True
