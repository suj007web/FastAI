"""PostgreSQL repository implementations for document, chunk, and embedding records."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from .contracts import (
    ChunkRecord,
    ChunkRepository,
    DocumentRecord,
    DocumentRepository,
    EmbeddingRecord,
    EmbeddingRepository,
)
from .models import ChunkModel, DocumentModel, EmbeddingModel


def _as_document_record(model: DocumentModel) -> DocumentRecord:
    return DocumentRecord(
        id=model.id,
        source_path=model.source_path,
        checksum=model.checksum,
        metadata=dict(model.metadata_json),
        created_at=model.created_at,
    )


def _as_chunk_record(model: ChunkModel) -> ChunkRecord:
    return ChunkRecord(
        id=model.id,
        document_id=model.document_id,
        chunk_index=model.chunk_index,
        text=model.text,
        metadata=dict(model.metadata_json),
    )


def _as_embedding_record(model: EmbeddingModel) -> EmbeddingRecord:
    vector_values = tuple(float(value) for value in model.vector)
    return EmbeddingRecord(
        id=model.id,
        chunk_id=model.chunk_id,
        values=vector_values,
        model=model.model,
        metadata=dict(model.metadata_json),
    )


@dataclass(frozen=True)
class PostgresRepositoryBundle:
    """Typed container for contract-compliant PostgreSQL repositories."""

    documents: PostgresDocumentRepository
    chunks: PostgresChunkRepository
    embeddings: PostgresEmbeddingRepository


@dataclass
class PostgresDocumentRepository(DocumentRepository):
    """PostgreSQL implementation of document persistence contract."""

    session: Session

    def upsert(self, document: DocumentRecord) -> DocumentRecord:
        model = self.session.get(DocumentModel, document.id)
        if model is None:
            model = DocumentModel(
                id=document.id,
                source_path=document.source_path,
                checksum=document.checksum,
                metadata_json=dict(document.metadata),
                created_at=document.created_at,
            )
            self.session.add(model)
        else:
            model.source_path = document.source_path
            model.checksum = document.checksum
            model.metadata_json = dict(document.metadata)
            model.created_at = document.created_at

        self.session.flush()
        return _as_document_record(model)

    def get(self, document_id: str) -> DocumentRecord | None:
        model = self.session.get(DocumentModel, document_id)
        if model is None:
            return None
        return _as_document_record(model)

    def list_ids(self) -> tuple[str, ...]:
        stmt = select(DocumentModel.id).order_by(DocumentModel.id)
        return tuple(self.session.scalars(stmt).all())


@dataclass
class PostgresChunkRepository(ChunkRepository):
    """PostgreSQL implementation of chunk persistence contract."""

    session: Session

    def upsert_many(self, chunks: tuple[ChunkRecord, ...]) -> tuple[ChunkRecord, ...]:
        persisted: list[ChunkRecord] = []
        for chunk in chunks:
            model = self.session.get(ChunkModel, chunk.id)
            if model is None:
                model = ChunkModel(
                    id=chunk.id,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    metadata_json=dict(chunk.metadata),
                )
                self.session.add(model)
            else:
                model.document_id = chunk.document_id
                model.chunk_index = chunk.chunk_index
                model.text = chunk.text
                model.metadata_json = dict(chunk.metadata)

            persisted.append(_as_chunk_record(model))

        self.session.flush()
        return tuple(persisted)

    def list_by_document(self, document_id: str) -> tuple[ChunkRecord, ...]:
        stmt = (
            select(ChunkModel)
            .where(ChunkModel.document_id == document_id)
            .order_by(ChunkModel.chunk_index, ChunkModel.id)
        )
        models = tuple(self.session.scalars(stmt).all())
        return tuple(_as_chunk_record(model) for model in models)


@dataclass
class PostgresEmbeddingRepository(EmbeddingRepository):
    """PostgreSQL implementation of embedding persistence contract."""

    session: Session

    def upsert_many(self, embeddings: tuple[EmbeddingRecord, ...]) -> tuple[EmbeddingRecord, ...]:
        persisted: list[EmbeddingRecord] = []
        for embedding in embeddings:
            model = self.session.get(EmbeddingModel, embedding.id)
            if model is None:
                model = EmbeddingModel(
                    id=embedding.id,
                    chunk_id=embedding.chunk_id,
                    model=embedding.model,
                    vector=list(embedding.values),
                    metadata_json=dict(embedding.metadata),
                )
                self.session.add(model)
            else:
                model.chunk_id = embedding.chunk_id
                model.model = embedding.model
                model.vector = list(embedding.values)
                model.metadata_json = dict(embedding.metadata)

            persisted.append(_as_embedding_record(model))

        self.session.flush()
        return tuple(persisted)

    def list_by_chunk_ids(self, chunk_ids: tuple[str, ...]) -> tuple[EmbeddingRecord, ...]:
        if not chunk_ids:
            return ()

        stmt = (
            select(EmbeddingModel)
            .where(EmbeddingModel.chunk_id.in_(chunk_ids))
            .order_by(EmbeddingModel.id)
        )
        models = tuple(self.session.scalars(stmt).all())
        return tuple(_as_embedding_record(model) for model in models)


def create_postgres_repositories(session: Session) -> PostgresRepositoryBundle:
    """Create contract-compliant PostgreSQL repositories from a SQLAlchemy session."""

    return PostgresRepositoryBundle(
        documents=PostgresDocumentRepository(session=session),
        chunks=PostgresChunkRepository(session=session),
        embeddings=PostgresEmbeddingRepository(session=session),
    )
