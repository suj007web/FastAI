from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastai import (
    ContextBuildResult,
    ContextSource,
    FastAI,
    FastAIConfig,
    GenerationResult,
    IngestionConfig,
    LLMConfig,
    PromptBuildResult,
    PromptSection,
    RetrievalConfig,
    RetrievedChunkCandidate,
    RuntimeConfig,
    VectorStoreConfig,
    mount_fastai_router,
)
from fastai.app.api.schemas import AskRequest
from fastai.ingestion import ChunkEmbeddingResult


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


def test_sdk_add_data_non_pgvector_does_not_require_pgvector_dsn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeVectorAdapter:
        def upsert(self, namespace: str, embeddings: tuple) -> None:
            return None

        def query(self, namespace: str, vector: tuple[float, ...], *, top_k: int, min_score: float):
            return ()

        def delete(self, namespace: str, embedding_ids: tuple[str, ...]) -> int:
            return 0

        def delete_namespace(self, namespace: str) -> int:
            return 0

    class _FakeEmbeddingAdapter:
        def embed_texts(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
            return tuple((1.0, 0.0, 0.0) for _ in texts)

        def embed_chunks(self, chunks):
            return tuple(
                ChunkEmbeddingResult(
                    text=chunk.text,
                    values=(1.0, 0.0, 0.0),
                    metadata=dict(chunk.metadata),
                )
                for chunk in chunks
            )

    sdk = FastAI(
        pgvector_dsn="",
        config=FastAIConfig(
            vector_store=VectorStoreConfig(backend="qdrant", pgvector_dsn=None),
            llm=LLMConfig(
                provider="openai",
                embedding_model="text-embedding-3-small",
                openai_api_key="sk-test",
            ),
        )
    )

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.txt").write_text("hello", encoding="utf-8")

    monkeypatch.setattr("fastai.sdk.select_vector_adapter", lambda *_args, **_kwargs: _FakeVectorAdapter())
    monkeypatch.setattr(sdk, "create_embedding_adapter", lambda: _FakeEmbeddingAdapter())

    summary = sdk.add_data(str(docs_dir))

    assert summary.processed == 1
    assert summary.failed == 0
    assert summary.documents == 1


def test_sdk_add_data_pgvector_requires_dsn(tmp_path: Path) -> None:
    sdk = FastAI(
        pgvector_dsn="",
        config=FastAIConfig(
            vector_store=VectorStoreConfig(backend="pgvector", pgvector_dsn=None),
            llm=LLMConfig(
                provider="openai",
                embedding_model="text-embedding-3-small",
                openai_api_key="sk-test",
            ),
        ),
    )

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.txt").write_text("hello", encoding="utf-8")

    with pytest.raises(ValueError, match="FASTAI_DB_DSN"):
        sdk.add_data(str(docs_dir))


def test_sdk_default_route_executes_orchestration_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    sdk = FastAI()

    monkeypatch.setattr(
        sdk,
        "retrieve",
        lambda *args, **kwargs: (
            RetrievedChunkCandidate(
                chunk_id="chunk-1",
                embedding_id="emb-1",
                score=0.9,
                metadata={"text": "source text", "source_path": "docs/a.txt"},
            ),
        ),
    )
    monkeypatch.setattr(
        sdk,
        "build_context",
        lambda *args, **kwargs: ContextBuildResult(
            context="source text",
            sources=(
                ContextSource(
                    id="chunk-1",
                    text="source text",
                    metadata={"source_path": "docs/a.txt"},
                ),
            ),
            token_count=2,
        ),
    )
    monkeypatch.setattr(
        sdk,
        "build_prompt",
        lambda *args, **kwargs: PromptBuildResult(
            final_prompt="[user_query]\nhello",
            sections=(PromptSection(name="user_query", content="hello"),),
        ),
    )
    monkeypatch.setattr(
        sdk,
        "generate",
        lambda *args, **kwargs: GenerationResult(
            text="generated answer",
            model="gpt-4.1-mini",
            provider="openai",
        ),
    )

    result = sdk.ask("hello")

    assert result["answer"] == "generated answer"
    assert isinstance(result["sources"], list)
    assert result["sources"][0]["id"] == "chunk-1"


def test_sdk_route_level_retrieval_overrides_are_forwarded(monkeypatch: pytest.MonkeyPatch) -> None:
    sdk = FastAI()
    captured: dict[str, object] = {}

    def fake_retrieve(
        query: str,
        *,
        top_k: int | None = None,
        min_score: float | None = None,
        dedupe_strategy: str = "chunk",
        source_paths: tuple[str, ...] | None = None,
        num_candidates: int | None = None,
    ) -> tuple[RetrievedChunkCandidate, ...]:
        captured["query"] = query
        captured["top_k"] = top_k
        captured["min_score"] = min_score
        captured["dedupe_strategy"] = dedupe_strategy
        captured["source_paths"] = source_paths
        captured["num_candidates"] = num_candidates
        return ()

    monkeypatch.setattr(sdk, "retrieve", fake_retrieve)
    monkeypatch.setattr(
        sdk,
        "build_context",
        lambda *args, **kwargs: ContextBuildResult(context="", sources=(), token_count=0),
    )
    monkeypatch.setattr(
        sdk,
        "build_prompt",
        lambda *args, **kwargs: PromptBuildResult(final_prompt="prompt", sections=()),
    )
    monkeypatch.setattr(
        sdk,
        "generate",
        lambda *args, **kwargs: GenerationResult(
            text="ok",
            model="gpt-4.1-mini",
            provider="openai",
        ),
    )

    payload = AskRequest(
        query="hello",
        top_k=7,
        min_score=0.25,
        num_candidates=80,
        dedupe_strategy="document",
        source_paths=("docs/a.txt",),
    )

    response = sdk.ask_payload(payload)

    assert response.answer == "ok"
    assert captured["query"] == "hello"
    assert captured["top_k"] == 7
    assert captured["min_score"] == 0.25
    assert captured["num_candidates"] == 80
    assert captured["dedupe_strategy"] == "document"
    assert captured["source_paths"] == ("docs/a.txt",)
