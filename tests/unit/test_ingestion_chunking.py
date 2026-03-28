from __future__ import annotations

from pathlib import Path

import pytest

from fastai.config import IngestionConfig
from fastai.ingestion import (
    ChunkingOptions,
    ExtractedDocument,
    chunk_extracted_documents,
    chunk_text,
    resolve_chunking_options,
)


def test_resolve_chunking_options_defaults_and_validation() -> None:
    defaults = resolve_chunking_options()
    assert defaults.chunk_size_tokens == 500
    assert defaults.chunk_overlap_tokens == 50

    explicit = resolve_chunking_options(
        IngestionConfig(chunk_size_tokens=8, chunk_overlap_tokens=2)
    )
    assert explicit == ChunkingOptions(chunk_size_tokens=8, chunk_overlap_tokens=2)

    with pytest.raises(ValueError, match="chunk_size_tokens"):
        resolve_chunking_options(IngestionConfig(chunk_size_tokens=0, chunk_overlap_tokens=0))

    with pytest.raises(ValueError, match="chunk_overlap_tokens"):
        resolve_chunking_options(IngestionConfig(chunk_size_tokens=8, chunk_overlap_tokens=-1))

    with pytest.raises(ValueError, match="less than chunk_size_tokens"):
        resolve_chunking_options(IngestionConfig(chunk_size_tokens=8, chunk_overlap_tokens=8))


def test_chunk_text_is_token_aware_and_deterministic() -> None:
    options = ChunkingOptions(chunk_size_tokens=4, chunk_overlap_tokens=1)
    source_text = "one two three four five six seven eight nine"

    first = chunk_text(source_text, source_path="docs/policy.txt", options=options)
    second = chunk_text(source_text, source_path="docs/policy.txt", options=options)

    assert first == second
    assert tuple(chunk.text for chunk in first) == (
        "one two three four",
        "four five six seven",
        "seven eight nine",
    )


def test_chunk_text_attaches_source_and_chunk_metadata_with_optional_page() -> None:
    options = ChunkingOptions(chunk_size_tokens=3, chunk_overlap_tokens=1)
    chunks = chunk_text(
        "alpha beta gamma delta",
        source_path=Path("docs/guide.pdf"),
        options=options,
        base_metadata={"page": 2},
    )

    assert len(chunks) == 2
    assert chunks[0].metadata["source_path"] == "docs/guide.pdf"
    assert chunks[0].metadata["chunk_index"] == 0
    assert chunks[0].metadata["page"] == 2
    assert chunks[1].metadata["chunk_index"] == 1


def test_chunk_extracted_documents_uses_stable_path_order() -> None:
    options = ChunkingOptions(chunk_size_tokens=2, chunk_overlap_tokens=0)
    documents = (
        ExtractedDocument(path=Path("b.txt"), text="b1 b2"),
        ExtractedDocument(path=Path("a.txt"), text="a1 a2"),
    )

    chunks = chunk_extracted_documents(documents, options=options)
    assert tuple(chunk.metadata["source_path"] for chunk in chunks) == ("a.txt", "b.txt")


def test_chunk_text_rejects_empty_payload() -> None:
    with pytest.raises(ValueError, match="empty text"):
        chunk_text("   \n\n", source_path="docs/empty.txt", options=ChunkingOptions(8, 2))