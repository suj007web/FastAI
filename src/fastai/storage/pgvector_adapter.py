"""pgvector adapter implementation backed by PostgreSQL embeddings table."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from .contracts import EmbeddingRecord, VectorQueryMatch, VectorStoreAdapter
from .models import EmbeddingModel
from .postgres_repositories import PostgresEmbeddingRepository


def _namespace_from_metadata(metadata: dict[str, object]) -> str | None:
    value = metadata.get("namespace")
    if isinstance(value, str):
        return value
    return None


@dataclass
class PgVectorAdapter(VectorStoreAdapter):
    """pgvector-backed vector adapter using embedding table persistence."""

    session: Session

    def upsert(self, namespace: str, embeddings: tuple[EmbeddingRecord, ...]) -> None:
        repo = PostgresEmbeddingRepository(session=self.session)
        namespaced = tuple(self._with_namespace(namespace, embedding) for embedding in embeddings)
        repo.upsert_many(namespaced)

    def query(
        self,
        namespace: str,
        vector: tuple[float, ...],
        *,
        top_k: int,
        min_score: float,
    ) -> tuple[VectorQueryMatch, ...]:
        stmt = select(EmbeddingModel)
        candidates = tuple(self.session.scalars(stmt).all())
        matches: list[VectorQueryMatch] = []

        for candidate in candidates:
            metadata = dict(candidate.metadata_json)
            if _namespace_from_metadata(metadata) != namespace:
                continue

            score = self._cosine(vector, tuple(float(value) for value in candidate.vector))
            if score < min_score:
                continue

            matches.append(
                VectorQueryMatch(
                    embedding_id=candidate.id,
                    chunk_id=candidate.chunk_id,
                    score=score,
                    metadata=metadata,
                )
            )

        matches.sort(key=lambda match: (-match.score, match.embedding_id))
        return tuple(matches[:top_k])

    def delete(self, namespace: str, embedding_ids: tuple[str, ...]) -> int:
        if not embedding_ids:
            return 0

        deleted = 0
        for embedding_id in embedding_ids:
            candidate = self.session.get(EmbeddingModel, embedding_id)
            if candidate is None:
                continue
            metadata = dict(candidate.metadata_json)
            if _namespace_from_metadata(metadata) != namespace:
                continue
            self.session.delete(candidate)
            deleted += 1

        self.session.flush()
        return deleted

    def delete_namespace(self, namespace: str) -> int:
        stmt = select(EmbeddingModel)
        candidates = tuple(self.session.scalars(stmt).all())
        deleted = 0
        for candidate in candidates:
            metadata = cast(dict[str, object], dict(candidate.metadata_json))
            if _namespace_from_metadata(metadata) != namespace:
                continue
            self.session.delete(candidate)
            deleted += 1

        self.session.flush()
        return deleted

    @staticmethod
    def _with_namespace(namespace: str, embedding: EmbeddingRecord) -> EmbeddingRecord:
        metadata = dict(embedding.metadata)
        metadata["namespace"] = namespace
        return EmbeddingRecord(
            id=embedding.id,
            chunk_id=embedding.chunk_id,
            values=embedding.values,
            model=embedding.model,
            metadata=metadata,
        )

    @staticmethod
    def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
        if len(left) != len(right):
            raise ValueError("Cannot compute cosine score for vectors of different lengths.")

        numerator = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = sqrt(sum(a * a for a in left))
        right_norm = sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)
