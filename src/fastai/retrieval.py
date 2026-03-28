"""Query embedding and vector search helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

from fastai.ingestion import EmbeddingAdapter
from fastai.storage import VectorQueryMatch, VectorStoreAdapter

RetrievalDedupeStrategy = Literal["none", "chunk", "document"]
SUPPORTED_RETRIEVAL_DEDUPE_STRATEGIES: tuple[RetrievalDedupeStrategy, ...] = (
    "none",
    "chunk",
    "document",
)


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
    dedupe_strategy: RetrievalDedupeStrategy = "chunk",
    source_paths: tuple[str, ...] | None = None,
    candidate_limit: int | None = None,
) -> tuple[RetrievedChunkCandidate, ...]:
    """Embed query text, then apply deterministic ranking and filtering policy.

    Policy order:
    1. Sort by descending score, then stable ids.
    2. Apply score threshold and optional source-path filtering.
    3. Apply optional deduplication strategy.
    4. Return top_k in stable deterministic order.
    """
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("Query must not be empty for retrieval.")
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    resolved_dedupe_strategy = _validate_dedupe_strategy(dedupe_strategy)
    query_limit = _resolve_candidate_limit(top_k=top_k, candidate_limit=candidate_limit)
    normalized_sources = _normalize_source_paths(source_paths)

    embedded_query = embedding_adapter.embed_texts((normalized_query,))
    if len(embedded_query) != 1:
        raise RuntimeError("Embedding adapter returned invalid query embedding response.")

    query_vector = embedded_query[0]
    matches = vector_adapter.query(
        namespace,
        query_vector,
        top_k=query_limit,
        min_score=min_score,
    )

    candidates = tuple(_to_candidate(match) for match in matches)
    return rank_and_filter_candidates(
        candidates,
        top_k=top_k,
        min_score=min_score,
        dedupe_strategy=resolved_dedupe_strategy,
        source_paths=normalized_sources,
    )


def rank_and_filter_candidates(
    candidates: tuple[RetrievedChunkCandidate, ...],
    *,
    top_k: int,
    min_score: float,
    dedupe_strategy: RetrievalDedupeStrategy = "chunk",
    source_paths: tuple[str, ...] | None = None,
) -> tuple[RetrievedChunkCandidate, ...]:
    """Apply deterministic score/source filtering and dedupe to candidates."""
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    resolved_dedupe_strategy = _validate_dedupe_strategy(dedupe_strategy)
    normalized_sources = _normalize_source_paths(source_paths)
    allowed_sources = set(normalized_sources) if normalized_sources else None

    ordered = tuple(
        sorted(candidates, key=lambda item: (-item.score, item.embedding_id, item.chunk_id))
    )

    filtered: list[RetrievedChunkCandidate] = []
    seen_chunk_ids: set[str] = set()
    seen_document_keys: set[str] = set()

    for candidate in ordered:
        if candidate.score < min_score:
            continue

        source_path = _candidate_source_path(candidate)
        if allowed_sources is not None and source_path not in allowed_sources:
            continue

        if resolved_dedupe_strategy == "chunk":
            if candidate.chunk_id in seen_chunk_ids:
                continue
            seen_chunk_ids.add(candidate.chunk_id)
        elif resolved_dedupe_strategy == "document":
            document_key = _candidate_document_key(candidate)
            if document_key in seen_document_keys:
                continue
            seen_document_keys.add(document_key)

        filtered.append(candidate)
        if len(filtered) >= top_k:
            break

    return tuple(filtered)


def _to_candidate(match: VectorQueryMatch) -> RetrievedChunkCandidate:
    return RetrievedChunkCandidate(
        chunk_id=match.chunk_id,
        embedding_id=match.embedding_id,
        score=match.score,
        metadata=dict(match.metadata),
    )


def _validate_dedupe_strategy(strategy: str) -> RetrievalDedupeStrategy:
    normalized = strategy.strip().lower()
    if normalized not in SUPPORTED_RETRIEVAL_DEDUPE_STRATEGIES:
        allowed = ", ".join(SUPPORTED_RETRIEVAL_DEDUPE_STRATEGIES)
        raise ValueError(
            f"Unsupported retrieval dedupe strategy '{strategy}'. Expected one of: {allowed}."
        )
    return cast(RetrievalDedupeStrategy, normalized)


def _resolve_candidate_limit(*, top_k: int, candidate_limit: int | None) -> int:
    if candidate_limit is None:
        return top_k
    if candidate_limit <= 0:
        raise ValueError("candidate_limit must be greater than zero when provided.")
    return max(top_k, candidate_limit)


def _normalize_source_paths(source_paths: tuple[str, ...] | None) -> tuple[str, ...] | None:
    if source_paths is None:
        return None

    normalized = tuple(path.strip() for path in source_paths if path.strip())
    if not normalized:
        return None
    return normalized


def _candidate_source_path(candidate: RetrievedChunkCandidate) -> str:
    value = candidate.metadata.get("source_path")
    if isinstance(value, str):
        return value
    return ""


def _candidate_document_key(candidate: RetrievedChunkCandidate) -> str:
    document_id = candidate.metadata.get("document_id")
    if isinstance(document_id, str) and document_id:
        return f"document_id:{document_id}"

    source_path = _candidate_source_path(candidate)
    if source_path:
        return f"source_path:{source_path}"

    return f"chunk_id:{candidate.chunk_id}"