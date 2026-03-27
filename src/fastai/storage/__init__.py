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
    "RouteDefinitionModel",
    "VectorQueryMatch",
    "VectorStoreAdapter",
]
