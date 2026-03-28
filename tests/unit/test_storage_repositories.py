from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from fastai.storage import (
    DEFAULT_VECTOR_DIMENSION,
    Base,
    ChunkRecord,
    DocumentRecord,
    EmbeddingRecord,
    StorageSessionManager,
    create_postgres_repositories,
)


def _vector(first: float, second: float) -> tuple[float, ...]:
    padding = (0.0,) * (DEFAULT_VECTOR_DIMENSION - 2)
    return (first, second, *padding)


@pytest.fixture
def postgres_session_manager() -> StorageSessionManager:
    dsn = os.getenv("FASTAI_TEST_DB_DSN")
    if not dsn:
        pytest.skip("Set FASTAI_TEST_DB_DSN to run PostgreSQL repository integration tests.")

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


def test_postgres_repositories_create_and_read(
    postgres_session_manager: StorageSessionManager,
) -> None:
    with postgres_session_manager.session_scope() as session:
        repositories = create_postgres_repositories(session)

        saved_document = repositories.documents.upsert(
            DocumentRecord(
                id="doc-1",
                source_path="docs/policy.txt",
                checksum="checksum-1",
                metadata={"type": "policy"},
            )
        )
        saved_chunks = repositories.chunks.upsert_many(
            (
                ChunkRecord(
                    id="chunk-2",
                    document_id="doc-1",
                    chunk_index=1,
                    text="paragraph 2",
                ),
                ChunkRecord(
                    id="chunk-1",
                    document_id="doc-1",
                    chunk_index=0,
                    text="paragraph 1",
                ),
            )
        )
        saved_embeddings = repositories.embeddings.upsert_many(
            (
                EmbeddingRecord(
                    id="emb-2",
                    chunk_id="chunk-2",
                    values=_vector(0.0, 1.0),
                    model="embed-v1",
                ),
                EmbeddingRecord(
                    id="emb-1",
                    chunk_id="chunk-1",
                    values=_vector(1.0, 0.0),
                    model="embed-v1",
                ),
            )
        )

        assert saved_document.id == "doc-1"
        assert tuple(chunk.id for chunk in saved_chunks) == ("chunk-2", "chunk-1")
        assert tuple(embedding.id for embedding in saved_embeddings) == ("emb-2", "emb-1")

    with postgres_session_manager.session_scope() as session:
        repositories = create_postgres_repositories(session)

        fetched_document = repositories.documents.get("doc-1")
        assert fetched_document is not None
        assert fetched_document.source_path == "docs/policy.txt"
        assert repositories.documents.list_ids() == ("doc-1",)
        assert tuple(chunk.id for chunk in repositories.chunks.list_by_document("doc-1")) == (
            "chunk-1",
            "chunk-2",
        )
        assert tuple(
            embedding.id
            for embedding in repositories.embeddings.list_by_chunk_ids(("chunk-1", "chunk-2"))
        ) == ("emb-1", "emb-2")


def test_postgres_session_scope_rolls_back_on_error(
    postgres_session_manager: StorageSessionManager,
) -> None:
    with pytest.raises(RuntimeError, match="force rollback"):
        with postgres_session_manager.session_scope() as session:
            repositories = create_postgres_repositories(session)
            repositories.documents.upsert(
                DocumentRecord(
                    id="doc-rollback",
                    source_path="docs/rollback.txt",
                    checksum="checksum-rollback",
                )
            )
            raise RuntimeError("force rollback")

    with postgres_session_manager.session_scope() as session:
        repositories = create_postgres_repositories(session)
        assert repositories.documents.get("doc-rollback") is None
        assert repositories.documents.list_ids() == ()
