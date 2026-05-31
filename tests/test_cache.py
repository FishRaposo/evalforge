"""Tests for the CachingBackend."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from evalforge.backends.base import BackendResponse, BaseBackend
from evalforge.backends.cache import CachingBackend


def _make_mock_backend() -> tuple[BaseBackend, AsyncMock]:
    mock = AsyncMock(spec=BaseBackend)
    mock.health_check = AsyncMock(return_value=True)
    return mock, mock


class TestCachingBackend:

    @pytest.mark.asyncio
    async def test_cache_miss_delegates_to_backend(self) -> None:
        mock_backend, mock_query = _make_mock_backend()
        mock_query.query = AsyncMock(return_value=BackendResponse(content="hello world", metadata={}))

        caching = CachingBackend(wrapped=mock_backend, max_size=100)

        response = await caching.query("test prompt")

        assert response.content == "hello world"
        mock_query.query.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_response(self) -> None:
        mock_backend, _ = _make_mock_backend()
        mock_backend.query = AsyncMock(return_value=BackendResponse(content="cached result", metadata={}))

        caching = CachingBackend(wrapped=mock_backend, max_size=100)

        await caching.query("test prompt")
        await caching.query("test prompt")

        assert mock_backend.query.await_count == 1

    @pytest.mark.asyncio
    async def test_cache_clear(self) -> None:
        mock_backend, _ = _make_mock_backend()
        mock_backend.query = AsyncMock(return_value=BackendResponse(content="result", metadata={}))

        caching = CachingBackend(wrapped=mock_backend, max_size=100)

        await caching.query("prompt a")
        caching.clear_cache()
        await caching.query("prompt a")

        assert mock_backend.query.await_count == 2

    @pytest.mark.asyncio
    async def test_max_size_eviction(self) -> None:
        mock_backend, _ = _make_mock_backend()
        mock_backend.query = AsyncMock(
            side_effect=lambda prompt, context=None: BackendResponse(
                content=f"response for {prompt}", metadata={}
            )
        )

        caching = CachingBackend(wrapped=mock_backend, max_size=2)

        await caching.query("prompt 1")
        await caching.query("prompt 2")
        await caching.query("prompt 3")

        first_response = await caching.query("prompt 1")

        assert mock_backend.query.await_count == 4
        assert first_response.content == "response for prompt 1"
