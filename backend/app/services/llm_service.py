"""LLM Service with Ollama and LM Studio provider support."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0  # seconds


async def retry_with_backoff(
    func,
    max_retries: int = MAX_RETRIES,
    base_delay: float = RETRY_DELAY_BASE,
):
    """Execute an async function with exponential backoff retry."""
    last_exception = None

    for attempt in range(max_retries):
        try:
            return await func()
        except httpx.HTTPError as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logger.warning(
                    f"LLM request failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"LLM request failed after {max_retries} attempts: {e}")

    raise last_exception


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Send a chat completion request and return the response content."""
        pass

    @abstractmethod
    def get_available_models(self) -> list[str]:
        """Return list of available models."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Send chat completion to Ollama with retry logic."""
        model = model or "llama3.2"

        async def _make_request():
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "")

        try:
            return await retry_with_backoff(_make_request)
        except Exception:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"LLM provider '{self.base_url}' is not reachable. "
                    f"Ensure Ollama is running at {self.base_url} or set LLM_PROVIDER=none in .env."
                ),
            )

    def get_available_models(self) -> list[str]:
        """Return list of available models from Ollama."""
        try:
            import httpx

            response = httpx.get(f"{self.base_url}/api/tags", timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.warning(f"Failed to get Ollama models: {e}")
            return []


class LMStudioProvider(LLMProvider):
    """LM Studio local LLM provider."""

    def __init__(self, base_url: str = "http://localhost:1234/v1"):
        self.base_url = base_url.rstrip("/")

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Send chat completion to LM Studio (OpenAI-compatible) with retry logic."""
        model = model or "llama-3.2-1b-instruct"

        async def _make_request():
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return (
                    data.get("choices", [{}])[0].get("message", {}).get("content", "")
                )

        try:
            return await retry_with_backoff(_make_request)
        except Exception:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"LLM provider '{self.base_url}' is not reachable. "
                    f"Ensure LM Studio is running at {self.base_url} or set LLM_PROVIDER=none in .env."
                ),
            )

    def get_available_models(self) -> list[str]:
        """Return list of available models from LM Studio."""
        try:
            import httpx

            response = httpx.get(f"{self.base_url}/models", timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return [m["id"] for m in data.get("data", [])]
        except Exception as e:
            logger.warning(f"Failed to get LM Studio models: {e}")
            return []


class LLMService:
    """Service that manages LLM providers and chat operations."""

    def __init__(
        self,
        provider: str = "ollama",
        model: str | None = None,
        base_url: str | None = None,
    ):
        self.provider_name = provider
        self.model = model
        if provider == "none":
            self._provider = None
        else:
            self._provider = self._create_provider(provider, base_url)

    def _create_provider(self, provider: str, base_url: str | None) -> LLMProvider:
        """Create an LLM provider instance based on provider name."""
        if provider == "lmstudio":
            return LMStudioProvider(base_url or "http://localhost:1234/v1")
        else:  # default to ollama
            return OllamaProvider(base_url or "http://localhost:11434")

    def is_available(self) -> bool:
        """Check if an LLM provider is configured."""
        return self._provider is not None

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
    ) -> str:
        """Send a chat message and get a response."""
        if self._provider is None:
            raise HTTPException(
                status_code=503,
                detail="No LLM provider configured. Set LLM_PROVIDER in .env to 'ollama' or 'lmstudio'.",
            )
        return await self._provider.chat(messages, model or self.model)

    def get_available_models(self) -> list[str]:
        """Get available models for the current provider."""
        if self._provider is None:
            return []
        return self._provider.get_available_models()


# Global LLM service instance (initialized at startup)
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        # Fallback to default if not initialized at startup
        _llm_service = LLMService()
    return _llm_service


def set_llm_service(service: LLMService) -> None:
    """Set the global LLM service instance (called from main.py)."""
    global _llm_service
    _llm_service = service
