"""Built-in and profile-level default values."""

from __future__ import annotations

from .types import (
    AuthConfig,
    IngestionConfig,
    LLMConfig,
    RetrievalConfig,
    RuntimeConfig,
    VectorStoreConfig,
)

BUILTIN_RUNTIME = RuntimeConfig(
    profile="balanced",
    env="development",
    host="0.0.0.0",
    port=8000,
    log_level="INFO",
    request_timeout_sec=60,
    enable_tracing=False,
    debug_payload_enabled=True,
)
BUILTIN_VECTOR = VectorStoreConfig(
    backend="pgvector",
    dimension=1536,
    namespace="default",
    pgvector_dsn="postgresql+psycopg://fastai:fastai@db:5432/fastai",
    qdrant_collection="fastai_chunks",
)
BUILTIN_RETRIEVAL = RetrievalConfig(
    top_k=5,
    min_score=0.0,
    num_candidates=50,
    max_context_tokens=3000,
)
BUILTIN_INGESTION = IngestionConfig(
    recursive=True,
    max_files=10000,
    include_globs=(),
    exclude_globs=(),
    failure_policy="continue",
    dedupe_mode="checksum_path",
    chunk_size_tokens=500,
    chunk_overlap_tokens=50,
)
BUILTIN_LLM = LLMConfig(
    provider="openai",
    model="gpt-4.1-mini",
    embedding_model="text-embedding-3-small",
    timeout_sec=30,
    max_retries=2,
)
BUILTIN_AUTH = AuthConfig(mode="disabled")

PROFILE_RUNTIME_OVERRIDES: dict[str, RuntimeConfig] = {
    "dev": RuntimeConfig(log_level="DEBUG"),
    "balanced": RuntimeConfig(),
    "quality": RuntimeConfig(),
    "latency": RuntimeConfig(log_level="WARNING"),
}
PROFILE_RETRIEVAL_OVERRIDES: dict[str, RetrievalConfig] = {
    "dev": RetrievalConfig(top_k=3, max_context_tokens=2000),
    "balanced": RetrievalConfig(),
    "quality": RetrievalConfig(top_k=8, max_context_tokens=4000),
    "latency": RetrievalConfig(top_k=3, max_context_tokens=1800),
}
PROFILE_LLM_OVERRIDES: dict[str, LLMConfig] = {
    "dev": LLMConfig(timeout_sec=20),
    "balanced": LLMConfig(),
    "quality": LLMConfig(timeout_sec=45),
    "latency": LLMConfig(timeout_sec=15),
}
