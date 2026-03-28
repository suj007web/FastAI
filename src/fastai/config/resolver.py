"""Config precedence resolver for the FastAI SDK."""

from __future__ import annotations

from .defaults import (
    BUILTIN_AUTH,
    BUILTIN_INGESTION,
    BUILTIN_LLM,
    BUILTIN_RETRIEVAL,
    BUILTIN_RUNTIME,
    BUILTIN_VECTOR,
    PROFILE_LLM_OVERRIDES,
    PROFILE_RETRIEVAL_OVERRIDES,
    PROFILE_RUNTIME_OVERRIDES,
)
from .env import env_auth, env_ingestion, env_llm, env_retrieval, env_runtime, env_vector
from .helpers import pick, pick_required
from .overrides import override_bool, override_csv, override_float, override_int, override_str
from .types import (
    AuthConfig,
    FastAIConfig,
    IngestionConfig,
    LLMConfig,
    ResolvedFastAIConfig,
    RetrievalConfig,
    RuntimeConfig,
    VectorStoreConfig,
)

SUPPORTED_INGESTION_FAILURE_POLICIES = frozenset({"continue", "fail_fast"})
SUPPORTED_INGESTION_DEDUPE_MODES = frozenset({"checksum_path", "checksum_only"})


def _normalize_csv(values: tuple[str, ...] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    return tuple(item.strip() for item in values if item.strip())


def _validate_ingestion(ingestion: IngestionConfig) -> IngestionConfig:
    if ingestion.max_files is None or ingestion.max_files <= 0:
        raise ValueError("Ingestion max_files must be greater than zero.")

    failure_policy = (ingestion.failure_policy or "").strip().lower()
    if failure_policy not in SUPPORTED_INGESTION_FAILURE_POLICIES:
        raise ValueError(
            "Unsupported ingestion failure_policy. Expected one of "
            f"{sorted(SUPPORTED_INGESTION_FAILURE_POLICIES)}; received '{failure_policy}'."
        )

    dedupe_mode = (ingestion.dedupe_mode or "").strip().lower()
    if dedupe_mode not in SUPPORTED_INGESTION_DEDUPE_MODES:
        raise ValueError(
            "Unsupported ingestion dedupe_mode. Expected one of "
            f"{sorted(SUPPORTED_INGESTION_DEDUPE_MODES)}; received '{dedupe_mode}'."
        )

    return IngestionConfig(
        recursive=ingestion.recursive,
        max_files=ingestion.max_files,
        include_globs=_normalize_csv(ingestion.include_globs),
        exclude_globs=_normalize_csv(ingestion.exclude_globs),
        failure_policy=failure_policy,
        dedupe_mode=dedupe_mode,
        chunk_size_tokens=ingestion.chunk_size_tokens,
        chunk_overlap_tokens=ingestion.chunk_overlap_tokens,
    )


def _normalize_profile(value: str | None) -> str:
    candidate = (value or BUILTIN_RUNTIME.profile or "balanced").strip().lower()
    if candidate in ("dev", "balanced", "quality", "latency"):
        return candidate
    return BUILTIN_RUNTIME.profile or "balanced"


def resolve_config(
    config: FastAIConfig | None = None,
    constructor_overrides: dict[str, object] | None = None,
) -> ResolvedFastAIConfig:
    """Resolve configuration with precedence: ctor > config > env > profile > built-in."""
    cfg = config or FastAIConfig()
    overrides = constructor_overrides or {}

    cfg_runtime = cfg.runtime or RuntimeConfig()
    cfg_vector = cfg.vector_store or VectorStoreConfig()
    cfg_retrieval = cfg.retrieval or RetrievalConfig()
    cfg_ingestion = cfg.ingestion or IngestionConfig()
    cfg_llm = cfg.llm or LLMConfig()
    cfg_auth = cfg.auth or AuthConfig()

    env_runtime_cfg = env_runtime()
    env_vector_cfg = env_vector()
    env_retrieval_cfg = env_retrieval()
    env_ingestion_cfg = env_ingestion()
    env_llm_cfg = env_llm()
    env_auth_cfg = env_auth()

    profile = _normalize_profile(
        pick(
            override_str(overrides, "profile"),
            cfg_runtime.profile,
            env_runtime_cfg.profile,
            BUILTIN_RUNTIME.profile,
        )
    )

    profile_runtime = PROFILE_RUNTIME_OVERRIDES[profile]
    profile_retrieval = PROFILE_RETRIEVAL_OVERRIDES[profile]
    profile_llm = PROFILE_LLM_OVERRIDES[profile]

    runtime = RuntimeConfig(
        profile=profile,
        env=pick_required(
            override_str(overrides, "env"),
            cfg_runtime.env,
            env_runtime_cfg.env,
            profile_runtime.env,
            BUILTIN_RUNTIME.env,
        ),
        host=pick_required(
            override_str(overrides, "host"),
            cfg_runtime.host,
            env_runtime_cfg.host,
            profile_runtime.host,
            BUILTIN_RUNTIME.host,
        ),
        port=pick_required(
            override_int(overrides, "port"),
            cfg_runtime.port,
            env_runtime_cfg.port,
            profile_runtime.port,
            BUILTIN_RUNTIME.port,
        ),
        log_level=pick_required(
            override_str(overrides, "log_level"),
            cfg_runtime.log_level,
            env_runtime_cfg.log_level,
            profile_runtime.log_level,
            BUILTIN_RUNTIME.log_level,
        ),
        request_timeout_sec=pick_required(
            override_int(overrides, "request_timeout_sec"),
            cfg_runtime.request_timeout_sec,
            env_runtime_cfg.request_timeout_sec,
            profile_runtime.request_timeout_sec,
            BUILTIN_RUNTIME.request_timeout_sec,
        ),
        enable_tracing=pick_required(
            override_bool(overrides, "enable_tracing"),
            cfg_runtime.enable_tracing,
            env_runtime_cfg.enable_tracing,
            profile_runtime.enable_tracing,
            BUILTIN_RUNTIME.enable_tracing,
        ),
        debug_payload_enabled=pick_required(
            override_bool(overrides, "debug_payload_enabled"),
            cfg_runtime.debug_payload_enabled,
            env_runtime_cfg.debug_payload_enabled,
            profile_runtime.debug_payload_enabled,
            BUILTIN_RUNTIME.debug_payload_enabled,
        ),
    )

    vector_store = VectorStoreConfig(
        backend=pick_required(
            override_str(overrides, "vector_backend", "backend"),
            cfg_vector.backend,
            env_vector_cfg.backend,
            BUILTIN_VECTOR.backend,
        ),
        dimension=pick_required(
            override_int(overrides, "dimension"),
            cfg_vector.dimension,
            env_vector_cfg.dimension,
            BUILTIN_VECTOR.dimension,
        ),
        namespace=pick_required(
            override_str(overrides, "namespace"),
            cfg_vector.namespace,
            env_vector_cfg.namespace,
            BUILTIN_VECTOR.namespace,
        ),
        pgvector_dsn=pick(
            override_str(overrides, "pgvector_dsn"),
            cfg_vector.pgvector_dsn,
            env_vector_cfg.pgvector_dsn,
            BUILTIN_VECTOR.pgvector_dsn,
        ),
        qdrant_url=pick(
            override_str(overrides, "qdrant_url"),
            cfg_vector.qdrant_url,
            env_vector_cfg.qdrant_url,
            BUILTIN_VECTOR.qdrant_url,
        ),
        qdrant_api_key=pick(
            override_str(overrides, "qdrant_api_key"),
            cfg_vector.qdrant_api_key,
            env_vector_cfg.qdrant_api_key,
            BUILTIN_VECTOR.qdrant_api_key,
        ),
        qdrant_collection=pick_required(
            override_str(overrides, "qdrant_collection"),
            cfg_vector.qdrant_collection,
            env_vector_cfg.qdrant_collection,
            BUILTIN_VECTOR.qdrant_collection,
        ),
        qdrant_distance=pick_required(
            override_str(overrides, "qdrant_distance"),
            cfg_vector.qdrant_distance,
            env_vector_cfg.qdrant_distance,
            BUILTIN_VECTOR.qdrant_distance,
        ),
        qdrant_timeout_sec=pick_required(
            override_int(overrides, "qdrant_timeout_sec"),
            cfg_vector.qdrant_timeout_sec,
            env_vector_cfg.qdrant_timeout_sec,
            BUILTIN_VECTOR.qdrant_timeout_sec,
        ),
        qdrant_prefer_grpc=pick_required(
            override_bool(overrides, "qdrant_prefer_grpc"),
            cfg_vector.qdrant_prefer_grpc,
            env_vector_cfg.qdrant_prefer_grpc,
            BUILTIN_VECTOR.qdrant_prefer_grpc,
        ),
        mongodb_uri=pick(
            override_str(overrides, "mongodb_uri"),
            cfg_vector.mongodb_uri,
            env_vector_cfg.mongodb_uri,
            BUILTIN_VECTOR.mongodb_uri,
        ),
        mongodb_database=pick(
            override_str(overrides, "mongodb_database"),
            cfg_vector.mongodb_database,
            env_vector_cfg.mongodb_database,
            BUILTIN_VECTOR.mongodb_database,
        ),
        mongodb_vector_collection=pick(
            override_str(overrides, "mongodb_vector_collection"),
            cfg_vector.mongodb_vector_collection,
            env_vector_cfg.mongodb_vector_collection,
            BUILTIN_VECTOR.mongodb_vector_collection,
        ),
        mongodb_vector_index_name=pick(
            override_str(overrides, "mongodb_vector_index_name"),
            cfg_vector.mongodb_vector_index_name,
            env_vector_cfg.mongodb_vector_index_name,
            BUILTIN_VECTOR.mongodb_vector_index_name,
        ),
        mongodb_vector_num_candidates=pick_required(
            override_int(overrides, "mongodb_vector_num_candidates"),
            cfg_vector.mongodb_vector_num_candidates,
            env_vector_cfg.mongodb_vector_num_candidates,
            BUILTIN_VECTOR.mongodb_vector_num_candidates,
        ),
        mongodb_vector_similarity=pick_required(
            override_str(overrides, "mongodb_vector_similarity"),
            cfg_vector.mongodb_vector_similarity,
            env_vector_cfg.mongodb_vector_similarity,
            BUILTIN_VECTOR.mongodb_vector_similarity,
        ),
    )

    retrieval = RetrievalConfig(
        top_k=pick_required(
            override_int(overrides, "top_k"),
            cfg_retrieval.top_k,
            env_retrieval_cfg.top_k,
            profile_retrieval.top_k,
            BUILTIN_RETRIEVAL.top_k,
        ),
        min_score=pick_required(
            override_float(overrides, "min_score"),
            cfg_retrieval.min_score,
            env_retrieval_cfg.min_score,
            profile_retrieval.min_score,
            BUILTIN_RETRIEVAL.min_score,
        ),
        num_candidates=pick_required(
            override_int(overrides, "num_candidates"),
            cfg_retrieval.num_candidates,
            env_retrieval_cfg.num_candidates,
            profile_retrieval.num_candidates,
            BUILTIN_RETRIEVAL.num_candidates,
        ),
        max_context_tokens=pick_required(
            override_int(overrides, "max_context_tokens"),
            cfg_retrieval.max_context_tokens,
            env_retrieval_cfg.max_context_tokens,
            profile_retrieval.max_context_tokens,
            BUILTIN_RETRIEVAL.max_context_tokens,
        ),
    )

    ingestion = IngestionConfig(
        recursive=pick_required(
            override_bool(overrides, "recursive"),
            cfg_ingestion.recursive,
            env_ingestion_cfg.recursive,
            BUILTIN_INGESTION.recursive,
        ),
        max_files=pick_required(
            override_int(overrides, "max_files"),
            cfg_ingestion.max_files,
            env_ingestion_cfg.max_files,
            BUILTIN_INGESTION.max_files,
        ),
        include_globs=pick_required(
            override_csv(overrides, "include_globs"),
            cfg_ingestion.include_globs,
            env_ingestion_cfg.include_globs,
            BUILTIN_INGESTION.include_globs,
        ),
        exclude_globs=pick_required(
            override_csv(overrides, "exclude_globs"),
            cfg_ingestion.exclude_globs,
            env_ingestion_cfg.exclude_globs,
            BUILTIN_INGESTION.exclude_globs,
        ),
        failure_policy=pick_required(
            override_str(overrides, "failure_policy"),
            cfg_ingestion.failure_policy,
            env_ingestion_cfg.failure_policy,
            BUILTIN_INGESTION.failure_policy,
        ),
        dedupe_mode=pick_required(
            override_str(overrides, "dedupe_mode"),
            cfg_ingestion.dedupe_mode,
            env_ingestion_cfg.dedupe_mode,
            BUILTIN_INGESTION.dedupe_mode,
        ),
        chunk_size_tokens=pick_required(
            override_int(overrides, "chunk_size_tokens"),
            cfg_ingestion.chunk_size_tokens,
            env_ingestion_cfg.chunk_size_tokens,
            BUILTIN_INGESTION.chunk_size_tokens,
        ),
        chunk_overlap_tokens=pick_required(
            override_int(overrides, "chunk_overlap_tokens"),
            cfg_ingestion.chunk_overlap_tokens,
            env_ingestion_cfg.chunk_overlap_tokens,
            BUILTIN_INGESTION.chunk_overlap_tokens,
        ),
    )
    ingestion = _validate_ingestion(ingestion)

    llm_provider = pick_required(
        override_str(overrides, "provider"),
        cfg_llm.provider,
        env_llm_cfg.provider,
        profile_llm.provider,
        BUILTIN_LLM.provider,
    )

    llm = LLMConfig(
        provider=llm_provider,
        model=pick_required(
            override_str(overrides, "model"),
            cfg_llm.model,
            env_llm_cfg.model,
            profile_llm.model,
            BUILTIN_LLM.model,
        ),
        embedding_model=pick_required(
            override_str(overrides, "embedding_model"),
            cfg_llm.embedding_model,
            env_llm_cfg.embedding_model,
            profile_llm.embedding_model,
            BUILTIN_LLM.embedding_model,
        ),
        timeout_sec=pick_required(
            override_int(overrides, "llm_timeout_sec", "timeout_sec"),
            cfg_llm.timeout_sec,
            env_llm_cfg.timeout_sec,
            profile_llm.timeout_sec,
            BUILTIN_LLM.timeout_sec,
        ),
        max_retries=pick_required(
            override_int(overrides, "max_retries"),
            cfg_llm.max_retries,
            env_llm_cfg.max_retries,
            profile_llm.max_retries,
            BUILTIN_LLM.max_retries,
        ),
        openai_api_key=pick(
            override_str(overrides, "openai_api_key"),
            cfg_llm.openai_api_key,
            env_llm_cfg.openai_api_key,
            profile_llm.openai_api_key,
            BUILTIN_LLM.openai_api_key,
        ),
        anthropic_api_key=pick(
            override_str(overrides, "anthropic_api_key"),
            cfg_llm.anthropic_api_key,
            env_llm_cfg.anthropic_api_key,
            profile_llm.anthropic_api_key,
            BUILTIN_LLM.anthropic_api_key,
        ),
    )

    provider_credential = override_str(overrides, "provider_credential")
    if provider_credential is not None:
        if llm.provider == "anthropic":
            llm = LLMConfig(
                provider=llm.provider,
                model=llm.model,
                embedding_model=llm.embedding_model,
                timeout_sec=llm.timeout_sec,
                max_retries=llm.max_retries,
                openai_api_key=llm.openai_api_key,
                anthropic_api_key=provider_credential,
            )
        else:
            llm = LLMConfig(
                provider=llm.provider,
                model=llm.model,
                embedding_model=llm.embedding_model,
                timeout_sec=llm.timeout_sec,
                max_retries=llm.max_retries,
                openai_api_key=provider_credential,
                anthropic_api_key=llm.anthropic_api_key,
            )

    auth = AuthConfig(
        mode=pick_required(
            override_str(overrides, "auth_mode", "mode"),
            cfg_auth.mode,
            env_auth_cfg.mode,
            BUILTIN_AUTH.mode,
        ),
        api_key=pick(
            override_str(overrides, "api_key"),
            cfg_auth.api_key,
            env_auth_cfg.api_key,
            BUILTIN_AUTH.api_key,
        ),
    )

    return ResolvedFastAIConfig(
        runtime=runtime,
        vector_store=vector_store,
        retrieval=retrieval,
        ingestion=ingestion,
        llm=llm,
        auth=auth,
    )
