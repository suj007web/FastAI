"""Context builder utilities for bounded prompt context assembly."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from .retrieval import RetrievedChunkCandidate


@dataclass(frozen=True)
class ContextSource:
    """Source citation payload derived from selected chunk candidates."""

    id: str
    text: str
    metadata: dict[str, object]


@dataclass(frozen=True)
class ContextBuildResult:
    """Bounded context assembly result."""

    context: str
    sources: tuple[ContextSource, ...]
    token_count: int


def build_context_payload(
    candidates: tuple[RetrievedChunkCandidate, ...],
    *,
    max_context_tokens: int,
    text_resolver: Callable[[RetrievedChunkCandidate], str] | None = None,
) -> ContextBuildResult:
    """Build bounded, deterministic context and citation-ready source mapping.

    The selection policy is deterministic:
    1. Candidates are sorted by score desc, embedding_id asc, chunk_id asc.
    2. Candidates with empty text are skipped.
    3. Candidates are included only when their text fits the remaining token budget.
    """
    if max_context_tokens <= 0:
        raise ValueError("max_context_tokens must be greater than zero.")

    resolver = text_resolver or _candidate_text
    ordered = tuple(
        sorted(candidates, key=lambda item: (-item.score, item.embedding_id, item.chunk_id))
    )

    selected_sources: list[ContextSource] = []
    token_total = 0

    for candidate in ordered:
        text = resolver(candidate).strip()
        if not text:
            continue

        chunk_tokens = estimate_text_tokens(text)
        if chunk_tokens <= 0:
            continue
        if token_total + chunk_tokens > max_context_tokens:
            continue

        selected_sources.append(
            ContextSource(
                id=candidate.chunk_id,
                text=text,
                metadata=_source_metadata(candidate),
            )
        )
        token_total += chunk_tokens

    context_text = "\n\n".join(source.text for source in selected_sources)
    return ContextBuildResult(
        context=context_text,
        sources=tuple(selected_sources),
        token_count=token_total,
    )


def estimate_text_tokens(text: str) -> int:
    """Estimate token count deterministically for budget enforcement."""
    normalized = text.strip()
    if not normalized:
        return 0
    return len(re.findall(r"\S+", normalized))


def _candidate_text(candidate: RetrievedChunkCandidate) -> str:
    text = candidate.metadata.get("text")
    if isinstance(text, str):
        return text

    chunk_text = candidate.metadata.get("chunk_text")
    if isinstance(chunk_text, str):
        return chunk_text

    return ""


def _source_metadata(candidate: RetrievedChunkCandidate) -> dict[str, object]:
    metadata = dict(candidate.metadata)
    metadata.setdefault("chunk_id", candidate.chunk_id)
    metadata.setdefault("embedding_id", candidate.embedding_id)
    metadata.setdefault("score", candidate.score)
    return metadata
