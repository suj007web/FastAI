"""Storage contracts and shared adapter interfaces."""

from .contracts import (
    ChunkRecord,
    ChunkRepository,
    DocumentRecord,
    DocumentRepository,
    EmbeddingRecord,
    EmbeddingRepository,
    VectorQueryMatch,
    VectorStoreAdapter,
)
from .models import (
    DEFAULT_VECTOR_DIMENSION,
    Base,
    ChunkModel,
    DocumentModel,
    EmbeddingModel,
    RouteDefinitionModel,
)
from .mongodb_adapter import MongoDBAtlasVectorAdapter
from .pgvector_adapter import PgVectorAdapter
from .postgres_repositories import (
    PostgresChunkRepository,
    PostgresDocumentRepository,
    PostgresEmbeddingRepository,
    PostgresRepositoryBundle,
    create_postgres_repositories,
)
from .qdrant_adapter import QdrantVectorAdapter
from .session import StorageSessionManager
from .vector_adapters import select_vector_adapter

__all__ = [
    "ChunkRecord",
    "ChunkModel",
    "ChunkRepository",
    "DEFAULT_VECTOR_DIMENSION",
    "DocumentRecord",
    "DocumentModel",
    "DocumentRepository",
    "EmbeddingRecord",
    "EmbeddingModel",
    "EmbeddingRepository",
    "Base",
    "MongoDBAtlasVectorAdapter",
    "PgVectorAdapter",
    "PostgresChunkRepository",
    "PostgresDocumentRepository",
    "PostgresEmbeddingRepository",
    "PostgresRepositoryBundle",
    "QdrantVectorAdapter",
    "RouteDefinitionModel",
    "StorageSessionManager",
    "VectorQueryMatch",
    "VectorStoreAdapter",
    "create_postgres_repositories",
    "select_vector_adapter",
]
