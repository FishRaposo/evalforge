"""OpenAI-compatible API backend."""

from __future__ import annotations

import time
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from evalforge.backends.base import BackendResponse, BaseBackend
from evalforge.config import get_settings


def _is_retryable_error(exc: BaseException) -> bool:
    """Return True for 429 or 5xx HTTP status errors."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code == 429 or exc.response.status_code >= 500
    return False


class OpenAICompatibleBackend(BaseBackend):
    """Backend that queries any OpenAI-compatible API.

    Supports OpenAI, Azure OpenAI, and local models via compatible
    APIs (e.g., Ollama, vLLM, LiteLLM).

    Args:
        api_key: Override for the configured API key.
        base_url: Override for the configured base URL.
        model: Override for the configured model name.
        timeout: Override for the request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """Initialize the OpenAI-compatible backend.

        Args:
            api_key: API key override.
            base_url: Base URL override.
            model: Model name override.
            timeout: Request timeout override in seconds.
        """
        settings = get_settings()
        self._api_key = api_key or settings.OPENAI_API_KEY
        self._base_url = base_url or settings.OPENAI_BASE_URL
        self._model = model or settings.OPENAI_MODEL
        self._timeout = timeout or settings.REQUEST_TIMEOUT

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception(_is_retryable_error),
    )
    async def query(
        self, prompt: str, context: dict[str, Any] | None = None
    ) -> BackendResponse:
        """Send a query to the OpenAI-compatible API.

        Args:
            prompt: The prompt to send.
            context: Optional context with conversation history or documents.

        Returns:
            A BackendResponse with the API response.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        start = time.monotonic()
        messages = self._build_messages(prompt, context)

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.0,
        }

        url = f"{self._base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

        elapsed = (time.monotonic() - start) * 1000
        return self._parse_response(response.json(), elapsed)

    async def health_check(self) -> bool:
        """Check if the OpenAI-compatible API is reachable.

        Returns:
            True if the API responds successfully, False otherwise.
        """
        try:
            url = f"{self._base_url}/models"
            headers = {"Authorization": f"Bearer {self._api_key}"}

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except (httpx.HTTPError, Exception):
            return False

    def _build_messages(
        self, prompt: str, context: dict[str, Any] | None = None
    ) -> list[dict[str, str]]:
        """Build the messages list for the OpenAI API call.

        Args:
            prompt: The user prompt.
            context: Optional context with prior conversation.

        Returns:
            A list of message dictionaries for the API.
        """
        messages: list[dict[str, str]] = []

        if context and "system" in context:
            messages.append({"role": "system", "content": context["system"]})

        if context and "conversation" in context:
            messages.extend(context["conversation"])

        messages.append({"role": "user", "content": prompt})
        return messages

    def _parse_response(
        self, response_data: dict[str, Any], elapsed_ms: float
    ) -> BackendResponse:
        """Parse the OpenAI API response into a BackendResponse.

        Args:
            response_data: The raw JSON response from the API.
            elapsed_ms: Time taken for the request in milliseconds.

        Returns:
            A BackendResponse with content and metadata.
        """
        choices = response_data.get("choices", [])
        content = ""
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")

        usage = response_data.get("usage", {})

        return BackendResponse(
            content=content,
            metadata={
                "model": response_data.get("model", self._model),
                "latency_ms": elapsed_ms,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        )
