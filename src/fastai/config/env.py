"""Environment-backed config readers."""

from __future__ import annotations

from os import getenv

from .helpers import parse_bool, parse_csv, parse_float, parse_int
from .types import (
    AuthConfig,
    IngestionConfig,
    LLMConfig,
    RetrievalConfig,
    RuntimeConfig,
    VectorStoreConfig,
)


def env_runtime() -> RuntimeConfig:
    """Load runtime config fields from environment variables."""
    return RuntimeConfig(
        profile=getenv("FASTAI_CONFIG_PROFILE"),
        env=getenv("FASTAI_ENV"),
        host=getenv("FASTAI_HOST"),
        port=parse_int(getenv("FASTAI_PORT")),
        log_level=getenv("FASTAI_LOG_LEVEL"),
        request_timeout_sec=parse_int(getenv("FASTAI_REQUEST_TIMEOUT_SEC")),
        enable_tracing=parse_bool(getenv("FASTAI_ENABLE_TRACING")),
        debug_payload_enabled=parse_bool(getenv("FASTAI_DEBUG_PAYLOAD_ENABLED")),
    )


def env_vector() -> VectorStoreConfig:
    """Load vector backend fields from environment variables."""
    return VectorStoreConfig(
        backend=getenv("FASTAI_VECTOR_BACKEND"),
        dimension=parse_int(getenv("FASTAI_VECTOR_DIMENSION")),
        namespace=getenv("FASTAI_VECTOR_NAMESPACE"),
        pgvector_dsn=getenv("FASTAI_DB_DSN"),
        qdrant_url=getenv("QDRANT_URL"),
        qdrant_collection=getenv("QDRANT_COLLECTION"),
        mongodb_uri=getenv("MONGODB_URI"),
        mongodb_database=getenv("MONGODB_DATABASE"),
        mongodb_vector_collection=getenv("MONGODB_VECTOR_COLLECTION"),
    )


def env_retrieval() -> RetrievalConfig:
    """Load retrieval fields from environment variables."""
    return RetrievalConfig(
        top_k=parse_int(getenv("FASTAI_RETRIEVAL_TOP_K")),
        min_score=parse_float(getenv("FASTAI_RETRIEVAL_MIN_SCORE")),
        num_candidates=parse_int(getenv("FASTAI_RETRIEVAL_NUM_CANDIDATES")),
        max_context_tokens=parse_int(getenv("FASTAI_MAX_CONTEXT_TOKENS")),
    )


def env_ingestion() -> IngestionConfig:
    """Load ingestion fields from environment variables."""
    return IngestionConfig(
        recursive=parse_bool(getenv("FASTAI_INGESTION_RECURSIVE")),
        max_files=parse_int(getenv("FASTAI_INGESTION_MAX_FILES")),
        include_globs=parse_csv(getenv("FASTAI_INGESTION_INCLUDE_GLOBS")),
        exclude_globs=parse_csv(getenv("FASTAI_INGESTION_EXCLUDE_GLOBS")),
        failure_policy=getenv("FASTAI_INGESTION_FAILURE_POLICY"),
        dedupe_mode=getenv("FASTAI_INGESTION_DEDUPE_MODE"),
        chunk_size_tokens=parse_int(getenv("FASTAI_CHUNK_SIZE_TOKENS")),
        chunk_overlap_tokens=parse_int(getenv("FASTAI_CHUNK_OVERLAP_TOKENS")),
    )


def env_llm() -> LLMConfig:
    """Load llm fields from environment variables."""
    return LLMConfig(
        provider=getenv("FASTAI_LLM_PROVIDER"),
        model=getenv("FASTAI_LLM_MODEL"),
        embedding_model=getenv("FASTAI_EMBEDDING_MODEL"),
        timeout_sec=parse_int(getenv("FASTAI_LLM_TIMEOUT_SEC")),
        max_retries=parse_int(getenv("FASTAI_LLM_MAX_RETRIES")),
        openai_api_key=getenv("OPENAI_API_KEY"),
        anthropic_api_key=getenv("ANTHROPIC_API_KEY"),
    )


def env_auth() -> AuthConfig:
    """Load auth fields from environment variables."""
    return AuthConfig(mode=getenv("FASTAI_API_AUTH_MODE"), api_key=getenv("FASTAI_API_KEY"))
