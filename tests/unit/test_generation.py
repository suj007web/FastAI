from __future__ import annotations

from types import SimpleNamespace

import pytest

from fastai.config import LLMConfig
from fastai.generation import (
    GenerationProviderError,
    LiteLLMGenerationProvider,
    create_generation_provider,
)


def test_litellm_generation_provider_generates_text_with_timeout_and_retries() -> None:
    captured: dict[str, object] = {}

    def fake_completion_client(**kwargs: object) -> object:
        captured.update(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="hello world"))]
        )

    provider = LiteLLMGenerationProvider(
        LLMConfig(
            provider="openai",
            model="gpt-4.1-mini",
            openai_api_key="sk-ok",
            timeout_sec=12,
            max_retries=3,
        ),
        completion_client=fake_completion_client,
    )

    result = provider.generate(
        "What is FastAI?",
        system_prompt="You are concise.",
        max_tokens=150,
        temperature=0.2,
    )

    assert result.text == "hello world"
    assert result.model == "gpt-4.1-mini"
    assert result.provider == "openai"
    assert captured["timeout"] == 12
    assert captured["num_retries"] == 3
    assert captured["max_tokens"] == 150
    assert captured["temperature"] == 0.2


def test_generation_provider_errors_are_structured() -> None:
    def failing_completion_client(**kwargs: object) -> object:
        raise RuntimeError("provider unavailable")

    provider = LiteLLMGenerationProvider(
        LLMConfig(
            provider="openai",
            model="gpt-4.1-mini",
            openai_api_key="sk-fail",
        ),
        completion_client=failing_completion_client,
    )

    with pytest.raises(GenerationProviderError) as exc_info:
        provider.generate("Hello")

    err = exc_info.value
    assert err.provider == "openai"
    assert err.model == "gpt-4.1-mini"
    assert "Generation request failed" in str(err)


def test_missing_openai_key_raises_actionable_error() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        LiteLLMGenerationProvider(LLMConfig(provider="openai", model="gpt-4.1-mini"))


def test_create_generation_provider_factory_returns_litellm_provider() -> None:
    provider = create_generation_provider(
        LLMConfig(
            provider="openai",
            model="gpt-4.1-mini",
            openai_api_key="sk-ok",
        ),
        completion_client=lambda **kwargs: SimpleNamespace(choices=[]),
    )
    assert isinstance(provider, LiteLLMGenerationProvider)
