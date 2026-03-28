from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastai import (
    FastAI,
    FastAIConfig,
    IngestionConfig,
    LLMConfig,
    RetrievalConfig,
    RuntimeConfig,
    VectorStoreConfig,
    mount_fastai_router,
)


def test_sdk_initializes_with_partial_config_objects() -> None:
    sdk = FastAI(
        config=FastAIConfig(
            runtime=RuntimeConfig(profile="balanced"),
            vector_store=VectorStoreConfig(backend="qdrant"),
            llm=LLMConfig(model="gpt-4.1-mini"),
        )
    )

    assert sdk.config.vector_store.backend == "qdrant"
    assert sdk.config.llm.model == "gpt-4.1-mini"
    assert sdk.config.retrieval.top_k == 5


def test_sdk_env_parity_with_matching_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FASTAI_VECTOR_BACKEND", "qdrant")
    monkeypatch.setenv("FASTAI_LLM_PROVIDER", "openai")
    monkeypatch.setenv("FASTAI_LLM_MODEL", "gpt-4.1-mini")

    sdk_env = FastAI.from_env()
    sdk_cfg = FastAI(
        config=FastAIConfig(
            vector_store=VectorStoreConfig(backend="qdrant"),
            llm=LLMConfig(provider="openai", model="gpt-4.1-mini"),
        )
    )

    assert sdk_env.config.vector_store.backend == sdk_cfg.config.vector_store.backend
    assert sdk_env.config.llm.provider == sdk_cfg.config.llm.provider
    assert sdk_env.config.llm.model == sdk_cfg.config.llm.model


def test_precedence_constructor_over_config_env_profile_built_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FASTAI_CONFIG_PROFILE", "latency")
    monkeypatch.setenv("FASTAI_RETRIEVAL_TOP_K", "4")

    sdk = FastAI(
        config=FastAIConfig(retrieval=RetrievalConfig(top_k=6)),
        profile="quality",
        top_k=9,
    )

    assert sdk.config.runtime.profile == "quality"
    assert sdk.config.retrieval.top_k == 9

    sdk_without_ctor_override = FastAI(
        config=FastAIConfig(retrieval=RetrievalConfig(top_k=6)),
        profile="quality",
    )
    assert sdk_without_ctor_override.config.retrieval.top_k == 6

    sdk_without_config_override = FastAI(profile="quality")
    assert sdk_without_config_override.config.retrieval.top_k == 4

    monkeypatch.delenv("FASTAI_RETRIEVAL_TOP_K")
    monkeypatch.delenv("FASTAI_CONFIG_PROFILE")
    sdk_profile_only = FastAI.from_profile("quality")
    assert sdk_profile_only.config.retrieval.top_k == 8


def test_constructor_matrix_builds_expected_instances() -> None:
    a = FastAI()
    b = FastAI(config=FastAIConfig(runtime=RuntimeConfig(profile="dev")))
    c = FastAI.from_env()
    d = FastAI.from_profile("latency", model="gpt-4.1-mini")
    e = FastAI.for_pgvector(
        dsn="postgresql+psycopg://fastai:fastai@db:5432/fastai",
        model="gpt-4.1-mini",
    )
    f = FastAI.for_qdrant(
        url="http://localhost:6333",
        collection="fastai_chunks",
        model="gpt-4.1-mini",
    )
    g = FastAI.for_mongodb_atlas(
        uri="mongodb+srv://example",
        database="fastai",
        collection="chunks",
        model="gpt-4.1-mini",
    )

    assert a.config.vector_store.backend == "pgvector"
    assert b.config.runtime.profile == "dev"
    assert c.config.runtime.profile in {"dev", "balanced", "quality", "latency"}
    assert d.config.runtime.profile == "latency"
    assert e.config.vector_store.backend == "pgvector"
    assert f.config.vector_store.backend == "qdrant"
    assert g.config.vector_store.backend == "mongodb_atlas"


def test_minimal_onboarding_backend_model_and_credential() -> None:
    sdk = FastAI(
        vector_backend="qdrant",
        model="gpt-4.1-mini",
        provider_credential="sk-test",
    )

    assert sdk.config.vector_store.backend == "qdrant"
    assert sdk.config.llm.model == "gpt-4.1-mini"
    assert sdk.config.llm.provider == "openai"
    assert sdk.config.llm.openai_api_key == "sk-test"


def test_sdk_library_mount_and_query_calls() -> None:
    sdk = FastAI()

    result = sdk.ask("What is the policy?")
    assert result["answer"] == "Query received: What is the policy?"

    app = FastAPI()
    mount_fastai_router(app, sdk=sdk, path="/ai")
    client = TestClient(app)

    response = client.post("/ai/ask", json={"query": "hello"})
    assert response.status_code == 200
    assert response.json()["answer"] == "Query received: hello"


def test_sdk_allows_custom_route_registration_and_execution() -> None:
    sdk = FastAI()

    @sdk.ai_route("/support", name="support")
    def support_handler(query: str) -> str:
        return f"support: {query}"

    response = sdk.ask("where", route_name="support")
    assert response["answer"] == "support: where"


def test_sdk_accepts_advanced_typed_sections() -> None:
    sdk = FastAI(
        config=FastAIConfig(
            ingestion=IngestionConfig(max_files=2000, failure_policy="fail_fast"),
            retrieval=RetrievalConfig(num_candidates=200),
        )
    )

    assert sdk.config.ingestion.max_files == 2000
    assert sdk.config.ingestion.failure_policy == "fail_fast"
    assert sdk.config.retrieval.num_candidates == 200


def test_sdk_validates_ingestion_failure_policy() -> None:
    with pytest.raises(ValueError, match="failure_policy"):
        FastAI(config=FastAIConfig(ingestion=IngestionConfig(failure_policy="abort")))


def test_sdk_validates_ingestion_dedupe_mode() -> None:
    with pytest.raises(ValueError, match="dedupe_mode"):
        FastAI(config=FastAIConfig(ingestion=IngestionConfig(dedupe_mode="none")))


def test_sdk_can_create_embedding_adapter_from_llm_config() -> None:
    sdk = FastAI(
        config=FastAIConfig(
            llm=LLMConfig(
                provider="openai",
                embedding_model="text-embedding-3-small",
                openai_api_key="sk-test",
            )
        )
    )

    adapter = sdk.create_embedding_adapter()
    assert adapter.__class__.__name__ == "LiteLLMEmbeddingAdapter"


def test_sdk_embedding_adapter_creation_requires_provider_key() -> None:
    sdk = FastAI(
        config=FastAIConfig(
            llm=LLMConfig(provider="openai", embedding_model="text-embedding-3-small")
        )
    )

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        sdk.create_embedding_adapter()
