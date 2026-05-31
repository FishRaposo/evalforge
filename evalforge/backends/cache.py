"""Caching wrapper for AI backends."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from evalforge.backends.base import BackendResponse, BaseBackend


class CachingBackend(BaseBackend):
    """Wraps any BaseBackend and caches responses in memory.

    Responses are cached by a hash of (prompt, context). When the
    cache reaches max_size the oldest entry is evicted.

    Args:
        wrapped: The underlying backend to delegate cache misses to.
        max_size: Maximum number of cached responses.
    """

    def __init__(self, wrapped: BaseBackend, max_size: int = 1000) -> None:
        """Initialize the caching backend.

        Args:
            wrapped: The backend instance to wrap.
            max_size: Maximum number of entries in the cache.
        """
        self._wrapped = wrapped
        self._max_size = max_size
        self._cache: dict[str, BackendResponse] = {}

    def _make_cache_key(
        self, prompt: str, context: dict[str, Any] | None = None
    ) -> str:
        """Compute a deterministic cache key from prompt and context.

        Args:
            prompt: The query prompt.
            context: Optional context dictionary.

        Returns:
            A hex digest string for use as a cache key.
        """
        key_data = json.dumps({"prompt": prompt, "context": context}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()

    async def query(
        self, prompt: str, context: dict[str, Any] | None = None
    ) -> BackendResponse:
        """Query the backend, returning a cached response if available.

        Args:
            prompt: The prompt to send.
            context: Optional context with conversation history or documents.

        Returns:
            A BackendResponse, either from cache or the wrapped backend.
        """
        cache_key = self._make_cache_key(prompt, context)
        if cache_key in self._cache:
            return self._cache[cache_key]

        response = await self._wrapped.query(prompt, context)

        if len(self._cache) >= self._max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        self._cache[cache_key] = response
        return response

    async def health_check(self) -> bool:
        """Check if the wrapped backend is healthy.

        Returns:
            True if the wrapped backend responds successfully.
        """
        return await self._wrapped.health_check()

    def clear_cache(self) -> None:
        """Remove all entries from the cache."""
        self._cache.clear()
