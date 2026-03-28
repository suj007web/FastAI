"""Qdrant vector store adapter implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import EmbeddingRecord, VectorQueryMatch, VectorStoreAdapter


def _distance_name(distance: str) -> str:
    return distance.strip().upper()


def _load_qdrant_models() -> Any:
    from qdrant_client.http import models as qmodels

    return qmodels


def _build_qdrant_client(
    url: str | None,
    api_key: str | None,
    timeout_sec: int | None,
    prefer_grpc: bool,
) -> Any:
    from qdrant_client import QdrantClient

    return QdrantClient(
        url=url,
        api_key=api_key,
        timeout=timeout_sec,
        prefer_grpc=prefer_grpc,
    )


def _qdrant_payload(embedding: EmbeddingRecord, namespace: str) -> dict[str, object]:
    return {
        "chunk_id": embedding.chunk_id,
        "model": embedding.model,
        "metadata": dict(embedding.metadata),
        "namespace": namespace,
    }


@dataclass
class QdrantVectorAdapter(VectorStoreAdapter):
    """Qdrant-backed implementation of the vector store contract."""

    url: str | None = None
    collection: str = "fastai_chunks"
    dimension: int = 1536
    api_key: str | None = None
    distance: str = "cosine"
    timeout_sec: int | None = None
    prefer_grpc: bool = False
    client: Any | None = None

    def __post_init__(self) -> None:
        if self.client is None:
            self.client = _build_qdrant_client(
                self.url,
                self.api_key,
                self.timeout_sec,
                self.prefer_grpc,
            )

    def _ensure_collection(self) -> None:
        client = self.client
        if client is None:
            raise RuntimeError("Qdrant client is not initialized.")

        qmodels = _load_qdrant_models()

        exists = False
        collection_exists = getattr(client, "collection_exists", None)
        if callable(collection_exists):
            exists = bool(collection_exists(collection_name=self.collection))
        else:
            try:
                client.get_collection(collection_name=self.collection)
                exists = True
            except Exception:
                exists = False

        if exists:
            return

        distance_enum = getattr(
            qmodels.Distance,
            _distance_name(self.distance),
            qmodels.Distance.COSINE,
        )
        client.create_collection(
            collection_name=self.collection,
            vectors_config=qmodels.VectorParams(size=self.dimension, distance=distance_enum),
        )

    def upsert(self, namespace: str, embeddings: tuple[EmbeddingRecord, ...]) -> None:
        self._ensure_collection()
        qmodels = _load_qdrant_models()

        points = [
            qmodels.PointStruct(
                id=embedding.id,
                vector=list(embedding.values),
                payload=_qdrant_payload(embedding, namespace),
            )
            for embedding in embeddings
        ]
        if not points:
            return

        client = self.client
        if client is None:
            raise RuntimeError("Qdrant client is not initialized.")

        client.upsert(collection_name=self.collection, points=points, wait=True)

    def query(
        self,
        namespace: str,
        vector: tuple[float, ...],
        *,
        top_k: int,
        min_score: float,
    ) -> tuple[VectorQueryMatch, ...]:
        self._ensure_collection()
        qmodels = _load_qdrant_models()

        query_filter = qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="namespace",
                    match=qmodels.MatchValue(value=namespace),
                )
            ]
        )

        client = self.client
        if client is None:
            raise RuntimeError("Qdrant client is not initialized.")

        results = client.search(
            collection_name=self.collection,
            query_vector=list(vector),
            query_filter=query_filter,
            limit=top_k,
            score_threshold=min_score,
            with_payload=True,
        )

        matches: list[VectorQueryMatch] = []
        for result in results:
            payload = dict(getattr(result, "payload", {}) or {})
            metadata = payload.get("metadata")
            if not isinstance(metadata, dict):
                metadata = {}

            chunk_id = payload.get("chunk_id")
            if not isinstance(chunk_id, str):
                chunk_id = ""

            embedding_id = result.id
            if not isinstance(embedding_id, str):
                embedding_id = str(embedding_id)

            score = float(getattr(result, "score", 0.0))
            matches.append(
                VectorQueryMatch(
                    embedding_id=embedding_id,
                    chunk_id=chunk_id,
                    score=score,
                    metadata=metadata,
                )
            )

        return tuple(matches)

    def _count_by_filter(self, query_filter: Any) -> int:
        client = self.client
        if client is None:
            raise RuntimeError("Qdrant client is not initialized.")

        count_response = client.count(
            collection_name=self.collection,
            count_filter=query_filter,
            exact=True,
        )
        count = getattr(count_response, "count", 0)
        return int(count)

    def delete(self, namespace: str, embedding_ids: tuple[str, ...]) -> int:
        self._ensure_collection()
        if not embedding_ids:
            return 0

        qmodels = _load_qdrant_models()
        query_filter = qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="namespace",
                    match=qmodels.MatchValue(value=namespace),
                ),
                qmodels.HasIdCondition(has_id=list(embedding_ids)),
            ]
        )
        deleted = self._count_by_filter(query_filter)

        if deleted:
            client = self.client
            if client is None:
                raise RuntimeError("Qdrant client is not initialized.")

            client.delete(
                collection_name=self.collection,
                points_selector=qmodels.FilterSelector(filter=query_filter),
                wait=True,
            )

        return deleted

    def delete_namespace(self, namespace: str) -> int:
        self._ensure_collection()
        qmodels = _load_qdrant_models()
        query_filter = qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="namespace",
                    match=qmodels.MatchValue(value=namespace),
                )
            ]
        )
        deleted = self._count_by_filter(query_filter)
        if deleted:
            client = self.client
            if client is None:
                raise RuntimeError("Qdrant client is not initialized.")

            client.delete(
                collection_name=self.collection,
                points_selector=qmodels.FilterSelector(filter=query_filter),
                wait=True,
            )

        return deleted
