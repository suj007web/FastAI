"""MongoDB Atlas vector store adapter implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import EmbeddingRecord, VectorQueryMatch, VectorStoreAdapter


def _build_mongo_client(uri: str) -> Any:
    from pymongo import MongoClient

    return MongoClient(uri)


@dataclass
class MongoDBAtlasVectorAdapter(VectorStoreAdapter):
    """MongoDB Atlas vector-search implementation of the vector store contract."""

    uri: str | None = None
    database: str | None = None
    collection: str = "chunks"
    vector_index_name: str = "vector_index"
    vector_field: str = "vector"
    num_candidates: int = 100
    similarity: str = "cosine"
    client: Any | None = None
    mongo_collection: Any | None = None

    def __post_init__(self) -> None:
        if self.mongo_collection is not None:
            return

        if self.client is None:
            if self.uri is None:
                raise ValueError("mongodb_atlas backend requires mongodb_uri to create a client.")
            self.client = _build_mongo_client(self.uri)

        if not self.database:
            raise ValueError("mongodb_atlas backend requires mongodb_database.")
        if not self.collection:
            raise ValueError("mongodb_atlas backend requires mongodb_vector_collection.")

        self.mongo_collection = self.client[self.database][self.collection]

    def upsert(self, namespace: str, embeddings: tuple[EmbeddingRecord, ...]) -> None:
        if not embeddings:
            return

        collection = self.mongo_collection
        if collection is None:
            raise RuntimeError("MongoDB collection is not initialized.")

        for embedding in embeddings:
            collection.update_one(
                {"_id": embedding.id},
                {
                    "$set": {
                        "chunk_id": embedding.chunk_id,
                        "model": embedding.model,
                        self.vector_field: list(embedding.values),
                        "metadata": dict(embedding.metadata),
                        "namespace": namespace,
                    }
                },
                upsert=True,
            )

    def query(
        self,
        namespace: str,
        vector: tuple[float, ...],
        *,
        top_k: int,
        min_score: float,
    ) -> tuple[VectorQueryMatch, ...]:
        pipeline = [
            {
                "$vectorSearch": {
                    "index": self.vector_index_name,
                    "path": self.vector_field,
                    "queryVector": list(vector),
                    "numCandidates": max(self.num_candidates, top_k),
                    "limit": top_k,
                    "filter": {"namespace": namespace},
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "chunk_id": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]
        collection = self.mongo_collection
        if collection is None:
            raise RuntimeError("MongoDB collection is not initialized.")

        rows = list(collection.aggregate(pipeline))

        matches: list[VectorQueryMatch] = []
        for row in rows:
            score = float(row.get("score", 0.0))
            if score < min_score:
                continue

            metadata = row.get("metadata")
            if not isinstance(metadata, dict):
                metadata = {}

            embedding_id = row.get("_id")
            if not isinstance(embedding_id, str):
                embedding_id = str(embedding_id)

            chunk_id = row.get("chunk_id")
            if not isinstance(chunk_id, str):
                chunk_id = ""

            matches.append(
                VectorQueryMatch(
                    embedding_id=embedding_id,
                    chunk_id=chunk_id,
                    score=score,
                    metadata=metadata,
                )
            )

        matches.sort(key=lambda match: (-match.score, match.embedding_id))
        return tuple(matches[:top_k])

    def delete(self, namespace: str, embedding_ids: tuple[str, ...]) -> int:
        if not embedding_ids:
            return 0

        collection = self.mongo_collection
        if collection is None:
            raise RuntimeError("MongoDB collection is not initialized.")

        result = collection.delete_many(
            {"namespace": namespace, "_id": {"$in": list(embedding_ids)}}
        )
        return int(getattr(result, "deleted_count", 0))

    def delete_namespace(self, namespace: str) -> int:
        collection = self.mongo_collection
        if collection is None:
            raise RuntimeError("MongoDB collection is not initialized.")

        result = collection.delete_many({"namespace": namespace})
        return int(getattr(result, "deleted_count", 0))
