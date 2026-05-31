"""Mock backend for testing and offline evaluation."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from evalforge.backends.base import BackendResponse, BaseBackend


class MockBackend(BaseBackend):
    """Backend that returns pre-configured responses for testing.

    Loads mock responses from a JSON file and matches them to
    incoming prompts based on pattern matching.

    Args:
        responses_file: Path to the JSON file with mock responses.
        default_response: Default response when no pattern matches.
    """

    def __init__(
        self,
        responses_file: Optional[Path] = None,
        default_response: str = "This is a mock response.",
    ) -> None:
        """Initialize the mock backend with optional response file.

        Args:
            responses_file: Path to JSON file with mock response mappings.
            default_response: Fallback response for unmatched prompts.
        """
        self._responses: dict[str, str] = {}
        self._default_response = default_response

        if responses_file and responses_file.exists():
            self._load_responses(responses_file)
        else:
            default_file = (
                Path(__file__).parent.parent.parent / "data" / "sample" / "mock_responses.json"
            )
            if default_file.exists():
                self._load_responses(default_file)

    async def query(
        self, prompt: str, context: Optional[dict[str, Any]] = None
    ) -> BackendResponse:
        """Return a mock response matching the prompt.

        Args:
            prompt: The prompt to match against mock responses.
            context: Ignored for mock backend.

        Returns:
            A BackendResponse with the matched or default response.
        """
        start = time.monotonic()

        response_text = self._default_response
        prompt_lower = prompt.lower().strip()

        for pattern, response in self._responses.items():
            if pattern.lower() in prompt_lower:
                response_text = response
                break

        elapsed = (time.monotonic() - start) * 1000

        return BackendResponse(
            content=response_text,
            metadata={
                "model": "mock",
                "latency_ms": elapsed,
                "mock": True,
            },
        )

    async def health_check(self) -> bool:
        """Mock backend is always healthy.

        Returns:
            Always True for the mock backend.
        """
        return True

    def _load_responses(self, path: Path) -> None:
        """Load mock responses from a JSON file.

        Args:
            path: Path to the JSON file containing response mappings.

        Raises:
            ValueError: If the file contains invalid JSON.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                self._responses = {
                    k: str(v) for k, v in data.items()
                }
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"Failed to load mock responses from {path}: {exc}") from exc

    def add_response(self, pattern: str, response: str) -> None:
        """Add a mock response pattern programmatically.

        Args:
            pattern: The pattern to match against prompts.
            response: The response to return for matching prompts.
        """
        self._responses[pattern] = response
