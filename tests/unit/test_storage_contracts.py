from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt

from fastai.storage import (
    ChunkRecord,
    DocumentRecord,
    EmbeddingRecord,
    VectorQueryMatch,
    VectorStoreAdapter,
)


@dataclass
class InMemoryDocumentRepository:
    _store: dict[str, DocumentRecord] = field(default_factory=dict)

    def upsert(self, document: DocumentRecord) -> DocumentRecord:
        self._store[document.id] = document
        return document

    def get(self, document_id: str) -> DocumentRecord | None:
        return self._store.get(document_id)

    def list_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._store.keys()))


@dataclass
class InMemoryChunkRepository:
    _store: dict[str, ChunkRecord] = field(default_factory=dict)

    def upsert_many(self, chunks: tuple[ChunkRecord, ...]) -> tuple[ChunkRecord, ...]:
        for chunk in chunks:
            self._store[chunk.id] = chunk
        return chunks

    def list_by_document(self, document_id: str) -> tuple[ChunkRecord, ...]:
        filtered = [chunk for chunk in self._store.values() if chunk.document_id == document_id]
        filtered.sort(key=lambda chunk: (chunk.chunk_index, chunk.id))
        return tuple(filtered)


@dataclass
class InMemoryEmbeddingRepository:
    _store: dict[str, EmbeddingRecord] = field(default_factory=dict)

    def upsert_many(self, embeddings: tuple[EmbeddingRecord, ...]) -> tuple[EmbeddingRecord, ...]:
        for embedding in embeddings:
            self._store[embedding.id] = embedding
        return embeddings

    def list_by_chunk_ids(self, chunk_ids: tuple[str, ...]) -> tuple[EmbeddingRecord, ...]:
        chunk_id_set = set(chunk_ids)
        filtered = [
            embedding
            for embedding in self._store.values()
            if embedding.chunk_id in chunk_id_set
        ]
        filtered.sort(key=lambda embedding: embedding.id)
        return tuple(filtered)


@dataclass
class InMemoryVectorAdapter:
    _namespaces: dict[str, dict[str, EmbeddingRecord]] = field(default_factory=dict)

    def upsert(self, namespace: str, embeddings: tuple[EmbeddingRecord, ...]) -> None:
        bucket = self._namespaces.setdefault(namespace, {})
        for embedding in embeddings:
            bucket[embedding.id] = embedding

    def query(
        self,
        namespace: str,
        vector: tuple[float, ...],
        *,
        top_k: int,
        min_score: float,
    ) -> tuple[VectorQueryMatch, ...]:
        bucket = self._namespaces.get(namespace, {})
        matches: list[VectorQueryMatch] = []
        for embedding in bucket.values():
            score = self._cosine(vector, embedding.values)
            if score < min_score:
                continue
            matches.append(
                VectorQueryMatch(
                    embedding_id=embedding.id,
                    chunk_id=embedding.chunk_id,
                    score=score,
                    metadata=embedding.metadata,
                )
            )

        matches.sort(key=lambda match: (-match.score, match.embedding_id))
        return tuple(matches[:top_k])

    def delete(self, namespace: str, embedding_ids: tuple[str, ...]) -> int:
        bucket = self._namespaces.get(namespace, {})
        deleted = 0
        for embedding_id in embedding_ids:
            if embedding_id in bucket:
                del bucket[embedding_id]
                deleted += 1
        return deleted

    def delete_namespace(self, namespace: str) -> int:
        bucket = self._namespaces.get(namespace, {})
        deleted = len(bucket)
        self._namespaces.pop(namespace, None)
        return deleted

    @staticmethod
    def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
        numerator = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = sqrt(sum(a * a for a in left))
        right_norm = sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)


def test_document_chunk_embedding_contracts_are_backend_agnostic() -> None:
    document_repo = InMemoryDocumentRepository()
    chunk_repo = InMemoryChunkRepository()
    embedding_repo = InMemoryEmbeddingRepository()

    document = DocumentRecord(id="doc-1", source_path="docs/policy.txt", checksum="abc123")
    stored_document = document_repo.upsert(document)

    chunks = (
        ChunkRecord(id="chunk-2", document_id="doc-1", chunk_index=1, text="paragraph 2"),
        ChunkRecord(id="chunk-1", document_id="doc-1", chunk_index=0, text="paragraph 1"),
    )
    stored_chunks = chunk_repo.upsert_many(chunks)

    embeddings = (
        EmbeddingRecord(id="emb-2", chunk_id="chunk-2", values=(0.0, 1.0), model="embed-v1"),
        EmbeddingRecord(id="emb-1", chunk_id="chunk-1", values=(1.0, 0.0), model="embed-v1"),
    )
    stored_embeddings = embedding_repo.upsert_many(embeddings)

    assert stored_document.id == "doc-1"
    assert document_repo.get("doc-1") is not None
    assert document_repo.list_ids() == ("doc-1",)
    assert tuple(chunk.id for chunk in stored_chunks) == ("chunk-2", "chunk-1")
    assert tuple(chunk.id for chunk in chunk_repo.list_by_document("doc-1")) == (
        "chunk-1",
        "chunk-2",
    )
    assert tuple(embedding.id for embedding in stored_embeddings) == ("emb-2", "emb-1")
    assert tuple(
        embedding.id for embedding in embedding_repo.list_by_chunk_ids(("chunk-1", "chunk-2"))
    ) == ("emb-1", "emb-2")


def test_vector_adapter_contract_enforces_namespace_query_and_delete() -> None:
    adapter: VectorStoreAdapter = InMemoryVectorAdapter()
    adapter.upsert(
        "ns-a",
        (
            EmbeddingRecord(id="emb-a", chunk_id="chunk-a", values=(1.0, 0.0), model="embed-v1"),
            EmbeddingRecord(id="emb-b", chunk_id="chunk-b", values=(0.8, 0.2), model="embed-v1"),
        ),
    )
    adapter.upsert(
        "ns-b",
        (EmbeddingRecord(id="emb-c", chunk_id="chunk-c", values=(0.0, 1.0), model="embed-v1"),),
    )

    matches = adapter.query("ns-a", (1.0, 0.0), top_k=2, min_score=0.1)

    assert tuple(match.embedding_id for match in matches) == ("emb-a", "emb-b")
    assert tuple(match.chunk_id for match in matches) == ("chunk-a", "chunk-b")

    deleted = adapter.delete("ns-a", ("emb-b", "missing"))
    assert deleted == 1

    remaining = adapter.query("ns-a", (1.0, 0.0), top_k=5, min_score=0.0)
    assert tuple(match.embedding_id for match in remaining) == ("emb-a",)

    removed_namespace_count = adapter.delete_namespace("ns-b")
    assert removed_namespace_count == 1
    assert adapter.query("ns-b", (0.0, 1.0), top_k=1, min_score=0.0) == ()
