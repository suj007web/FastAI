"""Storage and vector backend-agnostic contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol


@dataclass(frozen=True)
class DocumentRecord:
    """Canonical document metadata used by ingestion and retrieval flows."""

    id: str
    source_path: str
    checksum: str
    metadata: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class ChunkRecord:
    """Canonical chunk payload derived from a document."""

    id: str
    document_id: str
    chunk_index: int
    text: str
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddingRecord:
    """Embedding vector payload linked to a chunk."""

    id: str
    chunk_id: str
    values: tuple[float, ...]
    model: str
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class VectorQueryMatch:
    """Top-k vector query match with score and source identifiers."""

    embedding_id: str
    chunk_id: str
    score: float
    metadata: dict[str, object] = field(default_factory=dict)


class DocumentRepository(Protocol):
    """Persistence contract for document records."""

    def upsert(self, document: DocumentRecord) -> DocumentRecord:
        """Create or replace a document record by id."""

    def get(self, document_id: str) -> DocumentRecord | None:
        """Fetch a document by id."""

    def list_ids(self) -> tuple[str, ...]:
        """Return stable, deterministic document id listing."""


class ChunkRepository(Protocol):
    """Persistence contract for chunk records."""

    def upsert_many(self, chunks: tuple[ChunkRecord, ...]) -> tuple[ChunkRecord, ...]:
        """Create or replace chunks and return persisted values."""

    def list_by_document(self, document_id: str) -> tuple[ChunkRecord, ...]:
        """Return chunks for a document in deterministic chunk_index order."""


class EmbeddingRepository(Protocol):
    """Persistence contract for embedding records."""

    def upsert_many(self, embeddings: tuple[EmbeddingRecord, ...]) -> tuple[EmbeddingRecord, ...]:
        """Create or replace embeddings and return persisted values."""

    def list_by_chunk_ids(self, chunk_ids: tuple[str, ...]) -> tuple[EmbeddingRecord, ...]:
        """Return embeddings scoped to the provided chunk ids."""


class VectorStoreAdapter(Protocol):
    """Vector backend contract shared across pgvector/qdrant/mongodb implementations."""

    def upsert(self, namespace: str, embeddings: tuple[EmbeddingRecord, ...]) -> None:
        """Upsert embedding vectors under a namespace."""

    def query(
        self,
        namespace: str,
        vector: tuple[float, ...],
        *,
        top_k: int,
        min_score: float,
    ) -> tuple[VectorQueryMatch, ...]:
        """Return deterministic top-k matches sorted by descending score."""

    def delete(self, namespace: str, embedding_ids: tuple[str, ...]) -> int:
        """Delete embedding vectors by id and return deleted count."""

    def delete_namespace(self, namespace: str) -> int:
        """Delete all namespace vectors and return deleted count."""
