"""Deterministic token-aware chunking helpers for extracted text."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from fastai.config.defaults import BUILTIN_INGESTION
from fastai.config.types import IngestionConfig

from .extraction import ExtractedDocument, normalize_extracted_text

_TOKEN_RE = re.compile(r"\S+")


@dataclass(frozen=True)
class ChunkingOptions:
    """Resolved chunking controls for token-size and overlap policy."""

    chunk_size_tokens: int
    chunk_overlap_tokens: int


@dataclass(frozen=True)
class ChunkedText:
    """Token-window chunk payload with deterministic ordering metadata."""

    text: str
    metadata: dict[str, object]
    token_start: int
    token_end: int


def resolve_chunking_options(ingestion: IngestionConfig | None = None) -> ChunkingOptions:
    """Resolve and validate chunking policy from ingestion config."""
    cfg = ingestion or IngestionConfig()
    chunk_size = (
        cfg.chunk_size_tokens
        if cfg.chunk_size_tokens is not None
        else int(BUILTIN_INGESTION.chunk_size_tokens or 0)
    )
    chunk_overlap = (
        cfg.chunk_overlap_tokens
        if cfg.chunk_overlap_tokens is not None
        else int(BUILTIN_INGESTION.chunk_overlap_tokens or 0)
    )

    if chunk_size <= 0:
        raise ValueError("chunk_size_tokens must be greater than zero.")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap_tokens must be greater than or equal to zero.")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap_tokens must be less than chunk_size_tokens.")

    return ChunkingOptions(chunk_size_tokens=chunk_size, chunk_overlap_tokens=chunk_overlap)


def _build_chunk_metadata(
    *,
    source_path: str,
    chunk_index: int,
    base_metadata: dict[str, object] | None,
) -> dict[str, object]:
    metadata = {"source_path": source_path, "chunk_index": chunk_index}
    if base_metadata:
        metadata.update(base_metadata)
        metadata["source_path"] = source_path
        metadata["chunk_index"] = chunk_index
    return metadata


def chunk_text(
    text: str,
    *,
    source_path: str | Path,
    options: ChunkingOptions | None = None,
    base_metadata: dict[str, object] | None = None,
) -> tuple[ChunkedText, ...]:
    """Split normalized text into deterministic token windows with overlap."""
    resolved_options = options or resolve_chunking_options()
    normalized = normalize_extracted_text(text)
    matches = tuple(_TOKEN_RE.finditer(normalized))
    if not matches:
        raise ValueError("Cannot chunk empty text payload.")

    chunk_size = resolved_options.chunk_size_tokens
    overlap = resolved_options.chunk_overlap_tokens
    step = chunk_size - overlap

    chunks: list[ChunkedText] = []
    source = Path(source_path).as_posix()
    for chunk_index, token_start in enumerate(range(0, len(matches), step)):
        token_end = min(token_start + chunk_size, len(matches))
        char_start = matches[token_start].start()
        char_end = matches[token_end - 1].end()
        chunk_value = normalized[char_start:char_end]
        chunks.append(
            ChunkedText(
                text=chunk_value,
                metadata=_build_chunk_metadata(
                    source_path=source,
                    chunk_index=chunk_index,
                    base_metadata=base_metadata,
                ),
                token_start=token_start,
                token_end=token_end,
            )
        )
        if token_end == len(matches):
            break

    return tuple(chunks)


def chunk_extracted_documents(
    documents: tuple[ExtractedDocument, ...],
    *,
    options: ChunkingOptions | None = None,
) -> tuple[ChunkedText, ...]:
    """Chunk extracted documents in stable path order for deterministic output."""
    ordered = tuple(sorted(documents, key=lambda item: str(item.path.as_posix()).lower()))
    chunks: list[ChunkedText] = []
    for document in ordered:
        chunks.extend(
            chunk_text(
                document.text,
                source_path=document.path,
                options=options,
            )
        )
    return tuple(chunks)