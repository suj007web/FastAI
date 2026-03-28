"""Provider-agnostic LLM generation adapters."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol, cast

from fastai.config import LLMConfig


class FastAIGenerationError(RuntimeError):
    """Base internal generation error for FastAI runtime."""


class GenerationProviderError(FastAIGenerationError):
    """Structured provider failure with provider/model context."""

    def __init__(
        self,
        *,
        provider: str,
        model: str,
        message: str,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.model = model


@dataclass(frozen=True)
class GenerationResult:
    """Normalized generation output from provider implementations."""

    text: str
    model: str
    provider: str


class GenerationProvider(Protocol):
    """Provider-agnostic contract for text generation."""

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> GenerationResult:
        """Generate model output for a prompt."""


def _litellm_completion_call(**kwargs: object) -> object:
    from litellm import completion

    return completion(**cast(dict[str, Any], kwargs))


def _resolve_provider_api_key(config: LLMConfig) -> str:
    provider = (config.provider or "openai").strip().lower()
    if provider == "openai":
        if config.openai_api_key:
            return config.openai_api_key
        raise ValueError(
            "Missing API key for provider 'openai'. Set OPENAI_API_KEY or pass "
            "provider_credential to FastAI."
        )
    if provider == "anthropic":
        if config.anthropic_api_key:
            return config.anthropic_api_key
        raise ValueError(
            "Missing API key for provider 'anthropic'. Set ANTHROPIC_API_KEY or pass "
            "provider_credential to FastAI."
        )

    raise ValueError(
        f"Unsupported generation provider '{provider}'. Configure a supported provider."
    )


def _read_completion_text(response: object) -> str:
    if isinstance(response, dict):
        choices = response.get("choices")
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                message = first_choice.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content.strip()

        raise RuntimeError("Generation response did not include message content.")

    choices_attr = getattr(response, "choices", None)
    if isinstance(choices_attr, list) and choices_attr:
        first_choice = choices_attr[0]
        message_attr = getattr(first_choice, "message", None)
        content_attr = getattr(message_attr, "content", None)
        if isinstance(content_attr, str):
            return content_attr.strip()

    raise RuntimeError("Generation response did not include message content.")


class LiteLLMGenerationProvider(GenerationProvider):
    """LiteLLM-backed text generation provider."""

    def __init__(
        self,
        config: LLMConfig,
        *,
        completion_client: Callable[..., object] | None = None,
    ) -> None:
        self._provider = (config.provider or "openai").strip().lower()
        model = config.model
        if not model:
            raise ValueError("Missing model. Set FASTAI_LLM_MODEL before generation.")
        self._model = model

        self._api_key = _resolve_provider_api_key(config)
        self._timeout_sec = config.timeout_sec
        self._max_retries = config.max_retries
        self._completion_client = completion_client or _litellm_completion_call

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> GenerationResult:
        prompt_text = prompt.strip()
        if not prompt_text:
            raise ValueError("Prompt must not be empty for generation.")

        messages: list[dict[str, str]] = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": prompt_text})

        payload: dict[str, object] = {
            "model": self._model,
            "messages": messages,
            "api_key": self._api_key,
            "timeout": self._timeout_sec,
            "num_retries": self._max_retries,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature

        try:
            response = self._completion_client(**payload)
            text = _read_completion_text(response)
        except Exception as exc:
            raise GenerationProviderError(
                provider=self._provider,
                model=self._model,
                message=(
                    "Generation request failed. Verify provider credentials, model, "
                    f"and network access for provider '{self._provider}'."
                ),
            ) from exc

        if not text:
            raise GenerationProviderError(
                provider=self._provider,
                model=self._model,
                message="Generation response was empty.",
            )

        return GenerationResult(
            text=text,
            model=self._model,
            provider=self._provider,
        )


def create_generation_provider(
    config: LLMConfig,
    *,
    completion_client: Callable[..., object] | None = None,
) -> GenerationProvider:
    """Create configured generation provider implementation."""
    return LiteLLMGenerationProvider(config, completion_client=completion_client)
