"""Developer-first FastAI SDK facade."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from fastapi import APIRouter, FastAPI
from sqlalchemy.orm import Session

from .ai_app import AIApp, RouteHandler
from .app.api.schemas import AskRequest, AskResponse, DebugPayload, Source
from .config import FastAIConfig, resolve_config
from .context_builder import ContextBuildResult, build_context_payload
from .generation import (
    GenerationProvider,
    GenerationResult,
    create_generation_provider,
)
from .ingestion import EmbeddingAdapter, IngestionSummary, create_embedding_adapter, ingest_path
from .prompting import PromptBuildResult, assemble_prompt
from .retrieval import (
    RetrievalDedupeStrategy,
    RetrievedChunkCandidate,
    retrieve_chunk_candidates,
)
from .storage import (
    ChunkRecord,
    DocumentRecord,
    EmbeddingRecord,
    StorageSessionManager,
    VectorStoreAdapter,
    create_postgres_repositories,
    select_vector_adapter,
)


@dataclass
class _InMemoryDocumentRepository:
    """In-memory metadata store used when vector backend is not pgvector."""

    _items: dict[str, DocumentRecord]

    def upsert(self, document: DocumentRecord) -> DocumentRecord:
        self._items[document.id] = document
        return document

    def get(self, document_id: str) -> DocumentRecord | None:
        return self._items.get(document_id)

    def list_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))


@dataclass
class _InMemoryChunkRepository:
    """In-memory chunk store used for non-pgvector ingestion metadata."""

    _items: dict[str, ChunkRecord]

    def upsert_many(self, chunks: tuple[ChunkRecord, ...]) -> tuple[ChunkRecord, ...]:
        for chunk in chunks:
            self._items[chunk.id] = chunk
        return chunks

    def list_by_document(self, document_id: str) -> tuple[ChunkRecord, ...]:
        by_document = [item for item in self._items.values() if item.document_id == document_id]
        by_document.sort(key=lambda item: (item.chunk_index, item.id))
        return tuple(by_document)


@dataclass
class _InMemoryEmbeddingRepository:
    """In-memory embedding store used for non-pgvector ingestion metadata."""

    _items: dict[str, EmbeddingRecord]

    def upsert_many(
        self,
        embeddings: tuple[EmbeddingRecord, ...],
    ) -> tuple[EmbeddingRecord, ...]:
        for embedding in embeddings:
            self._items[embedding.id] = embedding
        return embeddings

    def list_by_chunk_ids(self, chunk_ids: tuple[str, ...]) -> tuple[EmbeddingRecord, ...]:
        if not chunk_ids:
            return ()
        chunk_id_set = set(chunk_ids)
        return tuple(item for item in self._items.values() if item.chunk_id in chunk_id_set)


@dataclass
class _InMemoryRepositoryBundle:
    """Contract-compliant metadata bundle for non-pgvector ingestion."""

    documents: _InMemoryDocumentRepository
    chunks: _InMemoryChunkRepository
    embeddings: _InMemoryEmbeddingRepository


def _create_in_memory_repositories() -> _InMemoryRepositoryBundle:
    return _InMemoryRepositoryBundle(
        documents=_InMemoryDocumentRepository(_items={}),
        chunks=_InMemoryChunkRepository(_items={}),
        embeddings=_InMemoryEmbeddingRepository(_items={}),
    )


class FastAI:
    """Facade that wraps runtime config, AI routes, and host integration hooks."""

    def __init__(
        self,
        *,
        config: FastAIConfig | None = None,
        profile: str | None = None,
        vector_backend: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        provider_credential: str | None = None,
        **overrides: object,
    ) -> None:
        constructor_overrides: dict[str, object] = {
            "profile": profile,
            "vector_backend": vector_backend,
            "model": model,
            "provider": provider,
            "provider_credential": provider_credential,
        }
        constructor_overrides.update(overrides)
        self.config = resolve_config(config=config, constructor_overrides=constructor_overrides)
        self._ai_app = AIApp()

        @self._ai_app.ai_route("/ask", name="ask")
        def _default_ask(query: str, payload: AskRequest) -> AskResponse:
            return self._orchestrate_ask(payload)

    @classmethod
    def from_env(cls) -> FastAI:
        """Create SDK instance using environment/profile/default resolution."""
        return cls()

    @classmethod
    def from_profile(cls, profile: str, **overrides: object) -> FastAI:
        """Create SDK instance from a profile plus explicit constructor overrides."""
        return cls(profile=profile, **cast(dict[str, Any], overrides))

    @classmethod
    def for_pgvector(
        cls,
        *,
        dsn: str,
        model: str,
        provider: str = "openai",
        provider_credential: str | None = None,
        **overrides: object,
    ) -> FastAI:
        """Create SDK instance preconfigured for pgvector backend."""
        extra = cast(dict[str, Any], overrides)
        return cls(
            vector_backend="pgvector",
            pgvector_dsn=dsn,
            model=model,
            provider=provider,
            provider_credential=provider_credential,
            **extra,
        )

    @classmethod
    def for_qdrant(
        cls,
        *,
        url: str,
        collection: str,
        model: str,
        provider: str = "openai",
        provider_credential: str | None = None,
        api_key: str | None = None,
        distance: str | None = None,
        timeout_sec: int | None = None,
        prefer_grpc: bool | None = None,
        **overrides: object,
    ) -> FastAI:
        """Create SDK instance preconfigured for qdrant backend."""
        extra = cast(dict[str, Any], overrides)
        return cls(
            vector_backend="qdrant",
            qdrant_url=url,
            qdrant_api_key=api_key,
            qdrant_collection=collection,
            qdrant_distance=distance,
            qdrant_timeout_sec=timeout_sec,
            qdrant_prefer_grpc=prefer_grpc,
            model=model,
            provider=provider,
            provider_credential=provider_credential,
            **extra,
        )

    @classmethod
    def for_mongodb_atlas(
        cls,
        *,
        uri: str,
        database: str,
        collection: str,
        model: str,
        provider: str = "openai",
        provider_credential: str | None = None,
        vector_index_name: str | None = None,
        num_candidates: int | None = None,
        similarity: str | None = None,
        **overrides: object,
    ) -> FastAI:
        """Create SDK instance preconfigured for MongoDB Atlas vector backend."""
        extra = cast(dict[str, Any], overrides)
        return cls(
            vector_backend="mongodb_atlas",
            mongodb_uri=uri,
            mongodb_database=database,
            mongodb_vector_collection=collection,
            mongodb_vector_index_name=vector_index_name,
            mongodb_vector_num_candidates=num_candidates,
            mongodb_vector_similarity=similarity,
            model=model,
            provider=provider,
            provider_credential=provider_credential,
            **extra,
        )

    def ai_route(
        self,
        path: str | None = None,
        *,
        name: str | None = None,
    ) -> Callable[[RouteHandler], RouteHandler]:
        """Register an AI route through the wrapped AIApp instance."""
        return self._ai_app.ai_route(path=path, name=name)

    def get_router(self) -> APIRouter:
        """Expose mountable router for plugin mode integration."""
        return self._ai_app.get_router()

    def mount(self, app: FastAPI, *, path: str = "/ai") -> None:
        """Mount FastAI routes into a host FastAPI app under a namespace path."""
        self._ai_app.include_in_app(app, prefix=path)

    def ask(self, query: str, *, debug: bool = False, route_name: str = "ask") -> dict[str, object]:
        """Synchronous library-style query helper."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            ask_response = asyncio.run(self.ask_async(query, debug=debug, route_name=route_name))
            return ask_response.model_dump()
        raise RuntimeError("FastAI.ask cannot be called inside an active event loop.")

    async def ask_async(
        self,
        query: str,
        *,
        debug: bool = False,
        route_name: str = "ask",
    ) -> AskResponse:
        """Async query helper using registered route handlers."""
        payload = AskRequest(query=query, debug=debug)
        return await self._ai_app.execute(route_name, payload)

    def ask_payload(self, payload: AskRequest, *, route_name: str = "ask") -> AskResponse:
        """Execute ask flow from a pre-validated request payload."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._ai_app.execute(route_name, payload))
        raise RuntimeError("FastAI.ask_payload cannot be called inside an active event loop.")

    def add_data(self, path: str) -> IngestionSummary:
        """Run full ingestion pipeline and persist indexed artifacts."""
        backend = (self.config.vector_store.backend or "").strip().lower()
        embedding_model = self.config.llm.embedding_model or self.config.llm.model
        if not embedding_model:
            raise ValueError("Embedding model is required for add_data ingestion.")

        if backend == "pgvector":
            dsn = self.config.vector_store.pgvector_dsn
            if not dsn:
                raise ValueError(
                    "FASTAI_DB_DSN (pgvector_dsn) is required for pgvector add_data ingestion."
                )

            manager = StorageSessionManager(dsn)
            with manager.session_scope() as session:
                repositories = create_postgres_repositories(session)
                vector_adapter = select_vector_adapter(
                    self.config.vector_store,
                    pgvector_session=session,
                )
                embedding_adapter = self.create_embedding_adapter()
                return ingest_path(
                    path=path,
                    namespace=self.config.vector_store.namespace or "default",
                    model_name=embedding_model,
                    ingestion_config=self.config.ingestion,
                    document_repo=repositories.documents,
                    chunk_repo=repositories.chunks,
                    embedding_repo=repositories.embeddings,
                    vector_adapter=vector_adapter,
                    embedding_adapter=embedding_adapter,
                    persist_embeddings_locally=False,
                )

        repositories = _create_in_memory_repositories()
        vector_adapter = select_vector_adapter(self.config.vector_store)
        embedding_adapter = self.create_embedding_adapter()
        return ingest_path(
            path=path,
            namespace=self.config.vector_store.namespace or "default",
            model_name=embedding_model,
            ingestion_config=self.config.ingestion,
            document_repo=repositories.documents,
            chunk_repo=repositories.chunks,
            embedding_repo=repositories.embeddings,
            vector_adapter=vector_adapter,
            embedding_adapter=embedding_adapter,
            persist_embeddings_locally=True,
        )

    def create_vector_adapter(self, *, session: Session | None = None) -> VectorStoreAdapter:
        """Create configured vector adapter for the active backend."""
        return select_vector_adapter(self.config.vector_store, pgvector_session=session)

    def create_embedding_adapter(self) -> EmbeddingAdapter:
        """Create configured embedding adapter for the active provider."""
        return create_embedding_adapter(self.config.llm)

    def create_generation_provider(self) -> GenerationProvider:
        """Create configured generation provider for the active provider/model."""
        return create_generation_provider(self.config.llm)

    def retrieve(
        self,
        query: str,
        *,
        top_k: int | None = None,
        min_score: float | None = None,
        dedupe_strategy: RetrievalDedupeStrategy = "chunk",
        source_paths: tuple[str, ...] | None = None,
        num_candidates: int | None = None,
    ) -> tuple[RetrievedChunkCandidate, ...]:
        """Run query embedding and vector search for top-k chunk candidates."""
        resolved_top_k = top_k if top_k is not None else int(self.config.retrieval.top_k or 0)
        resolved_min_score = (
            min_score if min_score is not None else float(self.config.retrieval.min_score or 0.0)
        )
        resolved_num_candidates = (
            num_candidates
            if num_candidates is not None
            else int(self.config.retrieval.num_candidates or resolved_top_k)
        )
        namespace = self.config.vector_store.namespace or "default"
        embedding_adapter = self.create_embedding_adapter()

        backend = (self.config.vector_store.backend or "").strip().lower()
        if backend == "pgvector":
            dsn = self.config.vector_store.pgvector_dsn
            if not dsn:
                raise ValueError(
                    "FASTAI_DB_DSN (pgvector_dsn) is required for pgvector retrieval."
                )

            manager = StorageSessionManager(dsn)
            with manager.session_scope() as session:
                vector_adapter = select_vector_adapter(
                    self.config.vector_store,
                    pgvector_session=session,
                )
                return retrieve_chunk_candidates(
                    query=query,
                    namespace=namespace,
                    embedding_adapter=embedding_adapter,
                    vector_adapter=vector_adapter,
                    top_k=resolved_top_k,
                    min_score=resolved_min_score,
                    dedupe_strategy=dedupe_strategy,
                    source_paths=source_paths,
                    candidate_limit=resolved_num_candidates,
                )

        vector_adapter = select_vector_adapter(self.config.vector_store)
        return retrieve_chunk_candidates(
            query=query,
            namespace=namespace,
            embedding_adapter=embedding_adapter,
            vector_adapter=vector_adapter,
            top_k=resolved_top_k,
            min_score=resolved_min_score,
            dedupe_strategy=dedupe_strategy,
            source_paths=source_paths,
            candidate_limit=resolved_num_candidates,
        )

    def build_context(
        self,
        candidates: tuple[RetrievedChunkCandidate, ...],
        *,
        max_context_tokens: int | None = None,
    ) -> ContextBuildResult:
        """Build bounded context text and source mapping from retrieval candidates."""
        resolved_max_context_tokens = (
            max_context_tokens
            if max_context_tokens is not None
            else int(self.config.retrieval.max_context_tokens or 0)
        )
        return build_context_payload(
            candidates,
            max_context_tokens=resolved_max_context_tokens,
        )

    def build_prompt(
        self,
        *,
        user_query: str,
        retrieved_context: str,
        system_instructions: str | None = None,
        route_instructions: str | None = None,
    ) -> PromptBuildResult:
        """Build deterministic final prompt from query, instructions, and context."""
        return assemble_prompt(
            user_query=user_query,
            retrieved_context=retrieved_context,
            system_instructions=system_instructions,
            route_instructions=route_instructions,
        )

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> GenerationResult:
        """Generate text through the configured provider implementation."""
        provider = self.create_generation_provider()
        return provider.generate(
            prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def summary(self) -> dict[str, object]:
        """Return resolved configuration as a serializable dictionary."""
        return {
            "runtime": self.config.runtime.__dict__,
            "vector_store": self.config.vector_store.__dict__,
            "retrieval": self.config.retrieval.__dict__,
            "ingestion": self.config.ingestion.__dict__,
            "llm": self.config.llm.__dict__,
            "auth": self.config.auth.__dict__,
        }

    def _orchestrate_ask(self, payload: AskRequest) -> AskResponse:
        query = payload.query.strip()

        dedupe_strategy: RetrievalDedupeStrategy = payload.dedupe_strategy or "chunk"

        candidates: tuple[RetrievedChunkCandidate, ...] = ()
        try:
            candidates = self.retrieve(
                query,
                top_k=payload.top_k,
                min_score=payload.min_score,
                dedupe_strategy=dedupe_strategy,
                source_paths=payload.source_paths,
                num_candidates=payload.num_candidates,
            )
        except Exception:
            candidates = ()

        context_result = self.build_context(
            candidates,
            max_context_tokens=payload.max_context_tokens,
        )
        prompt_result = self.build_prompt(
            user_query=query,
            retrieved_context=context_result.context,
            system_instructions=payload.system_instructions,
            route_instructions=payload.route_instructions,
        )

        answer_text = f"Query received: {query}"
        try:
            generated = self.generate(
                prompt_result.final_prompt,
                max_tokens=payload.max_tokens,
                temperature=payload.temperature,
            )
            answer_text = generated.text
        except Exception:
            answer_text = f"Query received: {query}"

        sources = [
            Source(id=source.id, text=source.text, metadata=dict(source.metadata))
            for source in context_result.sources
        ]

        debug_payload: DebugPayload | None = None
        if payload.debug and bool(self.config.runtime.debug_payload_enabled):
            debug_payload = DebugPayload(
                retrieved_chunks=[
                    {
                        "chunk_id": candidate.chunk_id,
                        "embedding_id": candidate.embedding_id,
                        "score": candidate.score,
                        "metadata": dict(candidate.metadata),
                    }
                    for candidate in candidates
                ],
                context=context_result.context,
                final_prompt=prompt_result.final_prompt,
            )

        return AskResponse(answer=answer_text, sources=sources, debug=debug_payload)


def mount_fastai_router(app: FastAPI, *, sdk: FastAI, path: str = "/ai") -> None:
    """Compatibility wrapper around the dedicated plugin mount entrypoint."""
    from .plugin import mount_fastai_router as plugin_mount_fastai_router

    plugin_mount_fastai_router(app, sdk=sdk, path=path)
