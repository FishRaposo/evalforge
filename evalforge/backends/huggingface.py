"""HuggingFace Inference API backend with offline-first fallback."""

from __future__ import annotations

import os
from typing import Any

from evalforge.backends.base import BackendResponse, BaseBackend
from evalforge.execution import SimulatedEvaluator


class HuggingFaceBackend(BaseBackend):
    """Backend for HuggingFace Inference API.

    Offline-first: returns simulated responses when no token is set.
    """

    def __init__(
        self,
        api_token: str | None = None,
        model: str = "meta-llama/Llama-2-7b-chat-hf",
    ) -> None:
        self._api_token = api_token or os.getenv("HF_API_TOKEN")
        self._model = model
        self._client: Any | None = None

    async def query(self, prompt: str, context: dict[str, Any] | None = None) -> BackendResponse:
        if not self._api_token:
            sim = SimulatedEvaluator(seed=hash(prompt) % 2**31)
            result = sim.evaluate(prompt)
            return BackendResponse(
                content=result["reasoning"],
                metadata={"method": "simulated", "model": self._model, "tokens_used": 0},
            )

        import httpx

        headers = {"Authorization": f"Bearer {self._api_token}"}
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 512, "temperature": 0.7},
        }
        url = f"https://api-inference.huggingface.co/models/{self._model}"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=60.0)
            response.raise_for_status()
            data = response.json()

        text = data[0]["generated_text"] if isinstance(data, list) else str(data)
        return BackendResponse(
            content=text,
            metadata={"model": self._model, "tokens_used": 0},
        )

    async def health_check(self) -> bool:
        return True
