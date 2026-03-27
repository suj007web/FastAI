"""Initial SQLAlchemy schema models for metadata and vector persistence."""

from __future__ import annotations

from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DEFAULT_VECTOR_DIMENSION = 1536


class Base(DeclarativeBase):
    """Declarative base for all storage schema models."""


class DocumentModel(Base):
    """Persisted source document metadata."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_documents_source_path", "source_path"),
        Index("ix_documents_created_at", "created_at"),
    )


class ChunkModel(Base):
    """Persisted chunk records derived from documents."""

    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, nullable=False)

    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_chunks_document_chunk_index"),
        Index("ix_chunks_document_id", "document_id"),
    )


class EmbeddingModel(Base):
    """Persisted vector embeddings for chunks."""

    __tablename__ = "embeddings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    chunk_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("chunks.id", ondelete="CASCADE"),
        nullable=False,
    )
    model: Mapped[str] = mapped_column(String(256), nullable=False)
    vector: Mapped[list[float]] = mapped_column(Vector(DEFAULT_VECTOR_DIMENSION), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_embeddings_chunk_id", "chunk_id"),
        Index("ix_embeddings_model", "model"),
        Index(
            "ix_embeddings_vector_ivfflat",
            "vector",
            postgresql_using="ivfflat",
            postgresql_ops={"vector": "vector_cosine_ops"},
            postgresql_with={"lists": 100},
        ),
    )


class RouteDefinitionModel(Base):
    """Persisted AI route definitions and per-route retrieval knobs."""

    __tablename__ = "route_definitions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    route_name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    route_path: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieval_top_k: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_route_definitions_route_name", "route_name"),
        Index("ix_route_definitions_route_path", "route_path"),
    )
