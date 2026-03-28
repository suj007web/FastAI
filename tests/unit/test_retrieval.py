from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from sqlalchemy import text

from fastai.ingestion import ChunkEmbeddingResult, EmbeddingAdapter
from fastai.ingestion.chunking import ChunkedText
from fastai.retrieval import RetrievedChunkCandidate, retrieve_chunk_candidates
from fastai.storage import (
    DEFAULT_VECTOR_DIMENSION,
    Base,
    ChunkRecord,
    DocumentRecord,
    EmbeddingRecord,
    StorageSessionManager,
    VectorQueryMatch,
    create_postgres_repositories,
)
from fastai.storage.pgvector_adapter import PgVectorAdapter


def _vector(first: float, second: float) -> tuple[float, ...]:
    padding = (0.0,) * (DEFAULT_VECTOR_DIMENSION - 2)
    return (first, second, *padding)


class _FakeEmbeddingAdapter(EmbeddingAdapter):
    def __init__(self, vector: tuple[float, ...]) -> None:
        self._vector = vector

    def embed_texts(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        return tuple(self._vector for _ in texts)

    def embed_chunks(
        self,
        chunks: tuple[ChunkedText, ...],
    ) -> tuple[ChunkEmbeddingResult, ...]:
        raise NotImplementedError()


class _FakeVectorAdapter:
    def __init__(self, matches: tuple[VectorQueryMatch, ...]) -> None:
        self._matches = matches

    def upsert(self, namespace: str, embeddings: tuple[EmbeddingRecord, ...]) -> None:
        return None

    def query(
        self,
        namespace: str,
        vector: tuple[float, ...],
        *,
        top_k: int,
        min_score: float,
    ) -> tuple[VectorQueryMatch, ...]:
        return self._matches

    def delete(self, namespace: str, embedding_ids: tuple[str, ...]) -> int:
        return 0

    def delete_namespace(self, namespace: str) -> int:
        return 0


@pytest.fixture
def postgres_session_manager() -> Generator[StorageSessionManager, None, None]:
    dsn = os.getenv("FASTAI_TEST_DB_DSN")
    if not dsn:
        pytest.skip("Set FASTAI_TEST_DB_DSN to run retrieval integration tests.")

    if "connect_timeout=" not in dsn:
        separator = "&" if "?" in dsn else "?"
        dsn = f"{dsn}{separator}connect_timeout=2"

    manager = StorageSessionManager(dsn)
    with manager.engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    Base.metadata.drop_all(bind=manager.engine)
    Base.metadata.create_all(bind=manager.engine)
    yield manager
    Base.metadata.drop_all(bind=manager.engine)


def test_retrieve_chunk_candidates_returns_deterministic_order() -> None:
    embedding_adapter = _FakeEmbeddingAdapter(_vector(1.0, 0.0))
    vector_adapter = _FakeVectorAdapter(
        (
            VectorQueryMatch(embedding_id="emb-2", chunk_id="chunk-b", score=0.8),
            VectorQueryMatch(embedding_id="emb-1", chunk_id="chunk-a", score=0.8),
            VectorQueryMatch(embedding_id="emb-3", chunk_id="chunk-c", score=0.2),
        )
    )

    candidates = retrieve_chunk_candidates(
        query="policy",
        namespace="default",
        embedding_adapter=embedding_adapter,
        vector_adapter=vector_adapter,
        top_k=2,
        min_score=0.0,
    )

    assert tuple(candidate.embedding_id for candidate in candidates) == ("emb-1", "emb-2")


def test_retrieve_chunk_candidates_pgvector_integration(
    postgres_session_manager: StorageSessionManager,
) -> None:
    with postgres_session_manager.session_scope() as session:
        repositories = create_postgres_repositories(session)
        repositories.documents.upsert(
            DocumentRecord(id="doc-1", source_path="docs/a.txt", checksum="checksum-a")
        )
        repositories.chunks.upsert_many(
            (
                ChunkRecord(id="chunk-a", document_id="doc-1", chunk_index=0, text="alpha info"),
                ChunkRecord(id="chunk-b", document_id="doc-1", chunk_index=1, text="beta info"),
            )
        )

        vector_adapter = PgVectorAdapter(session=session)
        vector_adapter.upsert(
            "default",
            (
                EmbeddingRecord(
                    id="emb-a",
                    chunk_id="chunk-a",
                    values=_vector(1.0, 0.0),
                    model="embed-v1",
                    metadata={"source_path": "docs/a.txt", "chunk_index": 0},
                ),
                EmbeddingRecord(
                    id="emb-b",
                    chunk_id="chunk-b",
                    values=_vector(0.0, 1.0),
                    model="embed-v1",
                    metadata={"source_path": "docs/a.txt", "chunk_index": 1},
                ),
            ),
        )

        candidates = retrieve_chunk_candidates(
            query="alpha question",
            namespace="default",
            embedding_adapter=_FakeEmbeddingAdapter(_vector(1.0, 0.0)),
            vector_adapter=vector_adapter,
            top_k=1,
            min_score=0.0,
        )

        assert len(candidates) == 1
        assert isinstance(candidates[0], RetrievedChunkCandidate)
        assert candidates[0].chunk_id == "chunk-a"