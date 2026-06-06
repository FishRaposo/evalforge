"""AI backends for query execution."""

from evalforge.backends.anthropic import AnthropicBackend
from evalforge.backends.base import BackendResponse, BaseBackend
from evalforge.backends.cache import CachingBackend
from evalforge.backends.huggingface import HuggingFaceBackend
from evalforge.backends.litellm import LiteLLMBackend
from evalforge.backends.mock import MockBackend
from evalforge.backends.openai_compatible import OpenAICompatibleBackend

__all__ = [
    "BaseBackend",
    "BackendResponse",
    "CachingBackend",
    "MockBackend",
    "OpenAICompatibleBackend",
    "AnthropicBackend",
    "HuggingFaceBackend",
    "LiteLLMBackend",
]
