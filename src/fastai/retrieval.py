"""Query embedding and vector search helpers."""

from __future__ import annotations

from dataclasses import dataclass

from fastai.ingestion import EmbeddingAdapter
from fastai.storage import VectorQueryMatch, VectorStoreAdapter


@dataclass(frozen=True)
class RetrievedChunkCandidate:
    """Ranked chunk candidate returned by retrieval search."""

    chunk_id: str
    embedding_id: str
    score: float
    metadata: dict[str, object]


def retrieve_chunk_candidates(
    *,
    query: str,
    namespace: str,
    embedding_adapter: EmbeddingAdapter,
    vector_adapter: VectorStoreAdapter,
    top_k: int,
    min_score: float,
) -> tuple[RetrievedChunkCandidate, ...]:
    """Embed query text and run deterministic top-k vector retrieval."""
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("Query must not be empty for retrieval.")
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    embedded_query = embedding_adapter.embed_texts((normalized_query,))
    if len(embedded_query) != 1:
        raise RuntimeError("Embedding adapter returned invalid query embedding response.")

    query_vector = embedded_query[0]
    matches = vector_adapter.query(
        namespace,
        query_vector,
        top_k=top_k,
        min_score=min_score,
    )

    candidates = tuple(_to_candidate(match) for match in matches)
    ordered = tuple(
        sorted(
            candidates,
            key=lambda item: (-item.score, item.embedding_id, item.chunk_id),
        )
    )
    return ordered[:top_k]


def _to_candidate(match: VectorQueryMatch) -> RetrievedChunkCandidate:
    return RetrievedChunkCandidate(
        chunk_id=match.chunk_id,
        embedding_id=match.embedding_id,
        score=match.score,
        metadata=dict(match.metadata),
    )