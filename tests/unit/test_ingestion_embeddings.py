from __future__ import annotations

from types import SimpleNamespace

import pytest

from fastai.config import LLMConfig
from fastai.ingestion import (
    ChunkedText,
    LiteLLMEmbeddingAdapter,
    create_embedding_adapter,
)


def test_litellm_embedding_adapter_generates_embeddings_for_all_chunks() -> None:
    chunks = (
        ChunkedText(
            text="alpha beta",
            metadata={"source_path": "docs/a.txt", "chunk_index": 0},
            token_start=0,
            token_end=2,
        ),
        ChunkedText(
            text="gamma delta",
            metadata={"source_path": "docs/a.txt", "chunk_index": 1},
            token_start=2,
            token_end=4,
        ),
    )

    def fake_embed_client(**kwargs: object) -> object:
        return SimpleNamespace(
            data=[
                SimpleNamespace(embedding=[0.1, 0.2, 0.3]),
                SimpleNamespace(embedding=[0.4, 0.5, 0.6]),
            ]
        )

    adapter = LiteLLMEmbeddingAdapter(
        LLMConfig(
            provider="openai",
            embedding_model="text-embedding-3-small",
            openai_api_key="sk-x",
        ),
        embed_client=fake_embed_client,
    )

    results = adapter.embed_chunks(chunks)
    assert len(results) == 2
    assert results[0].values == (0.1, 0.2, 0.3)
    assert results[1].values == (0.4, 0.5, 0.6)
    assert results[0].metadata["chunk_index"] == 0
    assert results[1].metadata["chunk_index"] == 1


def test_missing_openai_key_raises_actionable_error() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        LiteLLMEmbeddingAdapter(
            LLMConfig(provider="openai", embedding_model="text-embedding-3-small")
        )


def test_missing_anthropic_key_raises_actionable_error() -> None:
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        LiteLLMEmbeddingAdapter(
            LLMConfig(provider="anthropic", embedding_model="text-embedding-3-small")
        )


def test_invalid_key_or_provider_error_is_actionable() -> None:
    def failing_client(**kwargs: object) -> object:
        raise RuntimeError("401 unauthorized")

    adapter = LiteLLMEmbeddingAdapter(
        LLMConfig(
            provider="openai",
            embedding_model="text-embedding-3-small",
            openai_api_key="sk-bad",
        ),
        embed_client=failing_client,
    )

    with pytest.raises(RuntimeError, match="Verify provider credentials"):
        adapter.embed_texts(("hello",))


def test_create_embedding_adapter_factory_returns_litellm_adapter() -> None:
    adapter = create_embedding_adapter(
        LLMConfig(
            provider="openai",
            embedding_model="text-embedding-3-small",
            openai_api_key="sk-ok",
        ),
        embed_client=lambda **kwargs: SimpleNamespace(data=[]),
    )
    assert isinstance(adapter, LiteLLMEmbeddingAdapter)