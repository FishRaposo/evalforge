"""Abstract base class for AI backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field


class BackendResponse(BaseModel):
    """Response from an AI backend.

    Attributes:
        content: The text content of the response.
        metadata: Additional metadata (tokens, model, latency, etc.).
    """

    content: str = Field(..., description="Response text content")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Response metadata"
    )


class BaseBackend(ABC):
    """Abstract base class for all AI backends.

    Defines the interface for querying AI systems and checking
    their availability.
    """

    @abstractmethod
    async def query(
        self, prompt: str, context: Optional[dict[str, Any]] = None
    ) -> BackendResponse:
        """Send a query to the AI backend and return the response.

        Args:
            prompt: The prompt or question to send.
            context: Optional context for the query (e.g., retrieved documents).

        Returns:
            A BackendResponse with the AI response content and metadata.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the backend is available and responsive.

        Returns:
            True if the backend is healthy, False otherwise.
        """
        ...
