"""Typed SDK configuration data models."""

from __future__ import annotations

from dataclasses import dataclass

PROFILE_NAMES = ("dev", "balanced", "quality", "latency")


@dataclass(frozen=True)
class RuntimeConfig:
    """Runtime transport and app behavior settings."""

    profile: str | None = None
    env: str | None = None
    host: str | None = None
    port: int | None = None
    log_level: str | None = None
    request_timeout_sec: int | None = None
    enable_tracing: bool | None = None
    debug_payload_enabled: bool | None = None


@dataclass(frozen=True)
class VectorStoreConfig:
    """Vector backend and connection settings."""

    backend: str | None = None
    dimension: int | None = None
    namespace: str | None = None
    pgvector_dsn: str | None = None
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection: str | None = None
    qdrant_distance: str | None = None
    qdrant_timeout_sec: int | None = None
    qdrant_prefer_grpc: bool | None = None
    mongodb_uri: str | None = None
    mongodb_database: str | None = None
    mongodb_vector_collection: str | None = None
    mongodb_vector_index_name: str | None = None
    mongodb_vector_num_candidates: int | None = None
    mongodb_vector_similarity: str | None = None


@dataclass(frozen=True)
class RetrievalConfig:
    """Retrieval tuning settings."""

    top_k: int | None = None
    min_score: float | None = None
    num_candidates: int | None = None
    max_context_tokens: int | None = None


@dataclass(frozen=True)
class IngestionConfig:
    """Ingestion controls and chunking settings."""

    recursive: bool | None = None
    max_files: int | None = None
    include_globs: tuple[str, ...] | None = None
    exclude_globs: tuple[str, ...] | None = None
    failure_policy: str | None = None
    dedupe_mode: str | None = None
    chunk_size_tokens: int | None = None
    chunk_overlap_tokens: int | None = None


@dataclass(frozen=True)
class LLMConfig:
    """Generation and embedding provider configuration."""

    provider: str | None = None
    model: str | None = None
    embedding_model: str | None = None
    timeout_sec: int | None = None
    max_retries: int | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None


@dataclass(frozen=True)
class AuthConfig:
    """Request auth behavior settings."""

    mode: str | None = None
    api_key: str | None = None


@dataclass(frozen=True)
class FastAIConfig:
    """Top-level SDK config object for composition of typed sections."""

    runtime: RuntimeConfig | None = None
    vector_store: VectorStoreConfig | None = None
    retrieval: RetrievalConfig | None = None
    ingestion: IngestionConfig | None = None
    llm: LLMConfig | None = None
    auth: AuthConfig | None = None


@dataclass(frozen=True)
class ResolvedFastAIConfig:
    """Fully resolved SDK configuration after precedence application."""

    runtime: RuntimeConfig
    vector_store: VectorStoreConfig
    retrieval: RetrievalConfig
    ingestion: IngestionConfig
    llm: LLMConfig
    auth: AuthConfig
