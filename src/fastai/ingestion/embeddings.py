"""Embedding adapters for ingestion chunk payloads."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol, cast

from fastai.config import LLMConfig

from .chunking import ChunkedText


@dataclass(frozen=True)
class ChunkEmbeddingResult:
    """Embedding vector generated for one chunk payload."""

    text: str
    values: tuple[float, ...]
    metadata: dict[str, object]


class EmbeddingAdapter(Protocol):
    """Provider-agnostic contract for generating embedding vectors."""

    def embed_texts(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        """Return one embedding vector per input text in stable order."""

    def embed_chunks(self, chunks: tuple[ChunkedText, ...]) -> tuple[ChunkEmbeddingResult, ...]:
        """Return embedding vectors for chunk payloads preserving chunk order."""


def _litellm_embedding_call(**kwargs: object) -> object:
    from litellm import embedding

    return embedding(**cast(dict[str, Any], kwargs))


def _read_response_data(response: object) -> tuple[object, ...]:
    if isinstance(response, dict):
        data = response.get("data")
        if isinstance(data, list):
            return tuple(data)
        raise RuntimeError("Embedding response did not include a valid 'data' list.")

    data_attr = getattr(response, "data", None)
    if isinstance(data_attr, list):
        return tuple(data_attr)
    raise RuntimeError("Embedding response did not include a valid 'data' list.")


def _extract_embedding_values(item: object) -> tuple[float, ...]:
    if isinstance(item, dict):
        raw = item.get("embedding")
        if isinstance(raw, list):
            return tuple(float(value) for value in raw)
        raise RuntimeError("Embedding response item is missing 'embedding' vector.")

    embedding_attr = getattr(item, "embedding", None)
    if isinstance(embedding_attr, list):
        return tuple(float(value) for value in embedding_attr)
    raise RuntimeError("Embedding response item is missing 'embedding' vector.")


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
        "Unsupported embedding provider "
        f"'{provider}'. Configure a supported provider before creating embeddings."
    )


class LiteLLMEmbeddingAdapter(EmbeddingAdapter):
    """LiteLLM-based embedding adapter implementation."""

    def __init__(
        self,
        config: LLMConfig,
        *,
        embed_client: Callable[..., object] | None = None,
    ) -> None:
        self._config = config
        self._provider = (config.provider or "openai").strip().lower()
        self._model = config.embedding_model or config.model
        if not self._model:
            raise ValueError(
                "Missing embedding model. Set FASTAI_EMBEDDING_MODEL or "
                "FASTAI_LLM_MODEL."
            )

        self._api_key = _resolve_provider_api_key(config)
        self._timeout_sec = config.timeout_sec
        self._max_retries = config.max_retries
        self._embed_client = embed_client or _litellm_embedding_call

    def embed_texts(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        if not texts:
            return ()

        try:
            response = self._embed_client(
                model=self._model,
                input=list(texts),
                api_key=self._api_key,
                timeout=self._timeout_sec,
                num_retries=self._max_retries,
            )
            data = _read_response_data(response)
            vectors = tuple(_extract_embedding_values(item) for item in data)
        except Exception as exc:
            raise RuntimeError(
                "Embedding request failed. Verify provider credentials and embedding model "
                f"for provider '{self._provider}'."
            ) from exc

        if len(vectors) != len(texts):
            raise RuntimeError(
                "Embedding response length mismatch. "
                f"Expected {len(texts)} vectors but received {len(vectors)}."
            )
        return vectors

    def embed_chunks(self, chunks: tuple[ChunkedText, ...]) -> tuple[ChunkEmbeddingResult, ...]:
        texts = tuple(chunk.text for chunk in chunks)
        vectors = self.embed_texts(texts)
        return tuple(
            ChunkEmbeddingResult(
                text=chunk.text,
                values=vector,
                metadata=dict(chunk.metadata),
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        )


def create_embedding_adapter(
    config: LLMConfig,
    *,
    embed_client: Callable[..., object] | None = None,
) -> EmbeddingAdapter:
    """Create an embedding adapter implementation from LLM config."""
    return LiteLLMEmbeddingAdapter(config, embed_client=embed_client)