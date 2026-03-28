"""Vector backend selector wiring for storage adapters."""

from __future__ import annotations

from sqlalchemy.orm import Session

from fastai.config.types import VectorStoreConfig

from .contracts import VectorStoreAdapter
from .mongodb_adapter import MongoDBAtlasVectorAdapter
from .pgvector_adapter import PgVectorAdapter
from .qdrant_adapter import QdrantVectorAdapter


def select_vector_adapter(
    config: VectorStoreConfig,
    *,
    pgvector_session: Session | None = None,
) -> VectorStoreAdapter:
    """Select the configured vector adapter implementation."""

    backend = (config.backend or "").strip().lower()
    if backend == "pgvector":
        if pgvector_session is None:
            raise ValueError("pgvector backend requires an active SQLAlchemy session.")
        return PgVectorAdapter(session=pgvector_session)

    if backend == "qdrant":
        return QdrantVectorAdapter(
            url=config.qdrant_url,
            collection=config.qdrant_collection or "fastai_chunks",
            dimension=config.dimension or 1536,
            api_key=config.qdrant_api_key,
            distance=config.qdrant_distance or "cosine",
            timeout_sec=config.qdrant_timeout_sec,
            prefer_grpc=config.qdrant_prefer_grpc or False,
        )

    if backend == "mongodb_atlas":
        if not config.mongodb_database:
            raise ValueError("mongodb_atlas backend requires mongodb_database.")
        return MongoDBAtlasVectorAdapter(
            uri=config.mongodb_uri,
            database=config.mongodb_database,
            collection=config.mongodb_vector_collection or "chunks",
            vector_index_name=config.mongodb_vector_index_name or "vector_index",
            num_candidates=config.mongodb_vector_num_candidates or 100,
            similarity=config.mongodb_vector_similarity or "cosine",
        )

    raise ValueError(f"Unsupported vector backend '{backend}'.")
