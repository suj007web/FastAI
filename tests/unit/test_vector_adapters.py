from __future__ import annotations

import os
from dataclasses import dataclass
from math import sqrt
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from fastai.config.types import VectorStoreConfig
from fastai.storage import (
    DEFAULT_VECTOR_DIMENSION,
    Base,
    ChunkRecord,
    DocumentRecord,
    EmbeddingRecord,
    MongoDBAtlasVectorAdapter,
    PgVectorAdapter,
    QdrantVectorAdapter,
    StorageSessionManager,
    VectorStoreAdapter,
    create_postgres_repositories,
    select_vector_adapter,
)


def _vector(first: float, second: float) -> tuple[float, ...]:
    padding = (0.0,) * (DEFAULT_VECTOR_DIMENSION - 2)
    return (first, second, *padding)


def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


@dataclass
class _FakeQdrantPoint:
    id: str
    vector: tuple[float, ...]
    payload: dict[str, object]


class _FakeQdrantClient:
    def __init__(self) -> None:
        self.created = False
        self._points: dict[str, _FakeQdrantPoint] = {}

    def collection_exists(self, *, collection_name: str) -> bool:
        return self.created

    def create_collection(self, *, collection_name: str, vectors_config: object) -> None:
        self.created = True

    def upsert(self, *, collection_name: str, points: list[object], wait: bool) -> None:
        for point in points:
            self._points[str(point.id)] = _FakeQdrantPoint(
                id=str(point.id),
                vector=tuple(float(value) for value in point.vector),
                payload=dict(point.payload),
            )

    def search(
        self,
        *,
        collection_name: str,
        query_vector: list[float],
        query_filter: object,
        limit: int,
        score_threshold: float,
        with_payload: bool,
    ) -> list[SimpleNamespace]:
        namespace = query_filter.must[0].match.value
        query = tuple(float(value) for value in query_vector)
        results: list[SimpleNamespace] = []
        for point in self._points.values():
            if point.payload.get("namespace") != namespace:
                continue
            score = _cosine(query, point.vector)
            if score < score_threshold:
                continue
            results.append(SimpleNamespace(id=point.id, score=score, payload=point.payload))

        results.sort(key=lambda item: (-float(item.score), str(item.id)))
        return results[:limit]

    def count(self, *, collection_name: str, count_filter: object, exact: bool) -> SimpleNamespace:
        namespace = count_filter.must[0].match.value
        ids_filter = None
        if len(count_filter.must) > 1:
            ids_filter = set(str(value) for value in count_filter.must[1].has_id)

        count = 0
        for point in self._points.values():
            if point.payload.get("namespace") != namespace:
                continue
            if ids_filter is not None and point.id not in ids_filter:
                continue
            count += 1
        return SimpleNamespace(count=count)

    def delete(self, *, collection_name: str, points_selector: object, wait: bool) -> None:
        namespace = points_selector.filter.must[0].match.value
        ids_filter = None
        if len(points_selector.filter.must) > 1:
            ids_filter = set(str(value) for value in points_selector.filter.must[1].has_id)

        to_remove: list[str] = []
        for point in self._points.values():
            if point.payload.get("namespace") != namespace:
                continue
            if ids_filter is not None and point.id not in ids_filter:
                continue
            to_remove.append(point.id)

        for point_id in to_remove:
            self._points.pop(point_id, None)


class _FakeMongoResult:
    def __init__(self, deleted_count: int) -> None:
        self.deleted_count = deleted_count


class _FakeMongoCollection:
    def __init__(self) -> None:
        self._docs: dict[str, dict[str, object]] = {}

    def update_one(
        self,
        filter_spec: dict[str, object],
        update_spec: dict[str, object],
        upsert: bool,
    ) -> None:
        update_payload = update_spec["$set"]
        doc_id = str(filter_spec["_id"])
        self._docs[doc_id] = {
            "_id": doc_id,
            "chunk_id": update_payload["chunk_id"],
            "model": update_payload["model"],
            "vector": tuple(float(v) for v in update_payload["vector"]),
            "metadata": dict(update_payload["metadata"]),
            "namespace": update_payload["namespace"],
        }

    def aggregate(self, pipeline: list[dict[str, object]]) -> list[dict[str, object]]:
        stage = pipeline[0]["$vectorSearch"]
        namespace = stage["filter"]["namespace"]
        query = tuple(float(v) for v in stage["queryVector"])
        limit = int(stage["limit"])

        results: list[dict[str, object]] = []
        for doc in self._docs.values():
            if doc["namespace"] != namespace:
                continue
            score = _cosine(query, tuple(float(v) for v in doc["vector"]))
            results.append(
                {
                    "_id": doc["_id"],
                    "chunk_id": doc["chunk_id"],
                    "metadata": doc["metadata"],
                    "score": score,
                }
            )

        results.sort(key=lambda item: (-float(item["score"]), str(item["_id"])))
        return results[:limit]

    def delete_many(self, filter_spec: dict[str, object]) -> _FakeMongoResult:
        namespace = str(filter_spec.get("namespace", ""))
        ids_condition = filter_spec.get("_id")
        ids_filter: set[str] | None = None
        if isinstance(ids_condition, dict) and "$in" in ids_condition:
            ids_filter = set(str(value) for value in ids_condition["$in"])

        to_remove: list[str] = []
        for doc_id, doc in self._docs.items():
            if doc["namespace"] != namespace:
                continue
            if ids_filter is not None and doc_id not in ids_filter:
                continue
            to_remove.append(doc_id)

        for doc_id in to_remove:
            self._docs.pop(doc_id, None)

        return _FakeMongoResult(len(to_remove))


def _assert_vector_contract(adapter: VectorStoreAdapter) -> None:
    adapter.upsert(
        "ns-a",
        (
            EmbeddingRecord(
                id="emb-a",
                chunk_id="chunk-a",
                values=_vector(1.0, 0.0),
                model="embed-v1",
            ),
            EmbeddingRecord(
                id="emb-b",
                chunk_id="chunk-b",
                values=_vector(0.8, 0.2),
                model="embed-v1",
            ),
        ),
    )
    adapter.upsert(
        "ns-b",
        (
            EmbeddingRecord(
                id="emb-c",
                chunk_id="chunk-c",
                values=_vector(0.0, 1.0),
                model="embed-v1",
            ),
        ),
    )

    matches = adapter.query("ns-a", _vector(1.0, 0.0), top_k=2, min_score=0.1)
    assert tuple(match.embedding_id for match in matches) == ("emb-a", "emb-b")
    assert tuple(match.chunk_id for match in matches) == ("chunk-a", "chunk-b")

    deleted = adapter.delete("ns-a", ("emb-b", "missing"))
    assert deleted == 1

    remaining = adapter.query("ns-a", _vector(1.0, 0.0), top_k=5, min_score=0.0)
    assert tuple(match.embedding_id for match in remaining) == ("emb-a",)

    removed_namespace = adapter.delete_namespace("ns-b")
    assert removed_namespace == 1
    assert adapter.query("ns-b", _vector(0.0, 1.0), top_k=1, min_score=0.0) == ()


@pytest.fixture
def postgres_session_manager() -> StorageSessionManager:
    dsn = os.getenv("FASTAI_TEST_DB_DSN")
    if not dsn:
        pytest.skip("Set FASTAI_TEST_DB_DSN to run pgvector adapter integration tests.")

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


def test_qdrant_adapter_satisfies_vector_contract() -> None:
    adapter = QdrantVectorAdapter(
        url="http://localhost:6333",
        collection="fastai_chunks",
        client=_FakeQdrantClient(),
    )
    _assert_vector_contract(adapter)


def test_mongodb_atlas_adapter_satisfies_vector_contract() -> None:
    adapter = MongoDBAtlasVectorAdapter(
        uri="mongodb://localhost:27017",
        database="fastai",
        collection="chunks",
        mongo_collection=_FakeMongoCollection(),
    )
    _assert_vector_contract(adapter)


def test_pgvector_adapter_satisfies_vector_contract(
    postgres_session_manager: StorageSessionManager,
) -> None:
    with postgres_session_manager.session_scope() as session:
        repositories = create_postgres_repositories(session)
        repositories.documents.upsert(
            DocumentRecord(id="doc-1", source_path="docs/a.txt", checksum="checksum-doc")
        )
        repositories.chunks.upsert_many(
            (
                ChunkRecord(id="chunk-a", document_id="doc-1", chunk_index=0, text="alpha"),
                ChunkRecord(id="chunk-b", document_id="doc-1", chunk_index=1, text="beta"),
                ChunkRecord(id="chunk-c", document_id="doc-1", chunk_index=2, text="gamma"),
            )
        )

        adapter = PgVectorAdapter(session=session)
        _assert_vector_contract(adapter)


def test_select_vector_adapter_wires_backends() -> None:
    qdrant = select_vector_adapter(
        VectorStoreConfig(
            backend="qdrant",
            qdrant_url="http://localhost:6333",
            qdrant_collection="c",
        )
    )
    assert isinstance(qdrant, QdrantVectorAdapter)

    mongodb = select_vector_adapter(
        VectorStoreConfig(
            backend="mongodb_atlas",
            mongodb_uri="mongodb://localhost:27017",
            mongodb_database="fastai",
            mongodb_vector_collection="chunks",
        )
    )
    assert isinstance(mongodb, MongoDBAtlasVectorAdapter)

    with pytest.raises(ValueError, match="requires an active SQLAlchemy session"):
        select_vector_adapter(VectorStoreConfig(backend="pgvector"))


def test_select_vector_adapter_raises_for_unknown_backend() -> None:
    with pytest.raises(ValueError, match="Unsupported vector backend"):
        select_vector_adapter(VectorStoreConfig(backend="unknown"))
