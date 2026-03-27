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

__all__ = [
    "ChunkRecord",
    "ChunkRepository",
    "DocumentRecord",
    "DocumentRepository",
    "EmbeddingRecord",
    "EmbeddingRepository",
    "VectorQueryMatch",
    "VectorStoreAdapter",
]
