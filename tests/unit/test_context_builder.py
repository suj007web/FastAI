from __future__ import annotations

from fastai.context_builder import build_context_payload, estimate_text_tokens
from fastai.retrieval import RetrievedChunkCandidate


def test_build_context_payload_enforces_max_context_token_budget() -> None:
    candidates = (
        RetrievedChunkCandidate(
            chunk_id="chunk-a",
            embedding_id="emb-a",
            score=0.9,
            metadata={"text": "alpha beta gamma", "source_path": "docs/a.txt"},
        ),
        RetrievedChunkCandidate(
            chunk_id="chunk-b",
            embedding_id="emb-b",
            score=0.8,
            metadata={"text": "delta epsilon", "source_path": "docs/b.txt"},
        ),
    )

    result = build_context_payload(candidates, max_context_tokens=4)

    assert result.token_count <= 4
    assert tuple(source.id for source in result.sources) == ("chunk-a",)
    assert result.context == "alpha beta gamma"


def test_build_context_payload_uses_stable_score_ordering() -> None:
    # Input order is intentionally shuffled to prove deterministic ordering.
    candidates = (
        RetrievedChunkCandidate(
            chunk_id="chunk-b",
            embedding_id="emb-b",
            score=0.7,
            metadata={"text": "second", "source_path": "docs/b.txt"},
        ),
        RetrievedChunkCandidate(
            chunk_id="chunk-a",
            embedding_id="emb-a",
            score=0.9,
            metadata={"text": "first", "source_path": "docs/a.txt"},
        ),
    )

    result = build_context_payload(candidates, max_context_tokens=10)

    assert result.context == "first\n\nsecond"
    assert tuple(source.id for source in result.sources) == ("chunk-a", "chunk-b")


def test_build_context_payload_preserves_source_mapping_for_citations() -> None:
    candidate = RetrievedChunkCandidate(
        chunk_id="chunk-a",
        embedding_id="emb-a",
        score=0.93,
        metadata={
            "text": "citation chunk",
            "source_path": "docs/a.txt",
            "chunk_index": 2,
        },
    )

    result = build_context_payload((candidate,), max_context_tokens=10)

    assert result.context == "citation chunk"
    assert len(result.sources) == 1
    assert result.sources[0].id == "chunk-a"
    assert result.sources[0].metadata["source_path"] == "docs/a.txt"
    assert result.sources[0].metadata["chunk_index"] == 2
    assert result.sources[0].metadata["embedding_id"] == "emb-a"
    assert result.sources[0].metadata["score"] == 0.93


def test_estimate_text_tokens_counts_non_empty_segments() -> None:
    assert estimate_text_tokens("  one   two\nthree  ") == 3
    assert estimate_text_tokens("   ") == 0
