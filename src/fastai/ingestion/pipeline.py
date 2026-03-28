"""End-to-end ingestion orchestration for add_data."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass

from fastai.config.types import IngestionConfig
from fastai.storage import ChunkRecord, DocumentRecord, EmbeddingRecord
from fastai.storage.contracts import (
    ChunkRepository,
    DocumentRepository,
    EmbeddingRepository,
    VectorStoreAdapter,
)

from .chunking import chunk_extracted_documents, resolve_chunking_options
from .discovery import discover_ingestion_files, resolve_ingestion_discovery_options
from .embeddings import EmbeddingAdapter
from .extraction import extract_text_batch

LOGGER = logging.getLogger("fastai.ingestion")


@dataclass(frozen=True)
class IngestionSummary:
    """Summary counts returned by add_data ingestion runs."""

    processed: int
    skipped: int
    failed: int
    documents: int
    chunks: int
    embeddings: int


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _metadata_string(metadata: dict[str, object], key: str) -> str:
    value = metadata.get(key)
    if isinstance(value, str):
        return value
    return ""


def _metadata_int(metadata: dict[str, object], key: str) -> int:
    value = metadata.get(key)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


def ingest_path(
    *,
    path: str,
    namespace: str,
    model_name: str,
    ingestion_config: IngestionConfig,
    document_repo: DocumentRepository,
    chunk_repo: ChunkRepository,
    embedding_repo: EmbeddingRepository,
    vector_adapter: VectorStoreAdapter,
    embedding_adapter: EmbeddingAdapter,
    persist_embeddings_locally: bool,
) -> IngestionSummary:
    """Run discovery -> extraction -> chunking -> embedding -> persistence."""
    discovery_options = resolve_ingestion_discovery_options(ingestion_config)
    discovered_files = discover_ingestion_files(path, options=discovery_options)
    LOGGER.info(
        "ingestion_discovery path=%s discovered_supported=%d",
        path,
        len(discovered_files),
    )

    extraction = extract_text_batch(
        discovered_files,
        failure_policy=discovery_options.failure_policy,
    )
    LOGGER.info(
        "ingestion_extraction extracted=%d failed=%d",
        len(extraction.extracted),
        len(extraction.failures),
    )

    chunk_options = resolve_chunking_options(ingestion_config)
    chunked = chunk_extracted_documents(extraction.extracted, options=chunk_options)

    documents: list[DocumentRecord] = []
    chunks: list[ChunkRecord] = []
    for extracted in extraction.extracted:
        source_path = extracted.path.as_posix()
        document_checksum = _sha256(extracted.text)
        document_id = _sha256(f"{source_path}:{document_checksum}")[:64]
        documents.append(
            DocumentRecord(
                id=document_id,
                source_path=source_path,
                checksum=document_checksum,
                metadata={"path": source_path},
            )
        )

    document_by_path = {document.source_path: document for document in documents}
    for chunk in chunked:
        source_path = _metadata_string(chunk.metadata, "source_path")
        parent = document_by_path.get(source_path)
        if parent is None:
            continue
        chunk_index = _metadata_int(chunk.metadata, "chunk_index")
        chunk_id = _sha256(f"{parent.id}:{chunk_index}:{chunk.text}")[:64]
        chunks.append(
            ChunkRecord(
                id=chunk_id,
                document_id=parent.id,
                chunk_index=chunk_index,
                text=chunk.text,
                metadata=dict(chunk.metadata),
            )
        )

    for document in documents:
        document_repo.upsert(document)
    chunk_repo.upsert_many(tuple(chunks))

    chunked_for_embeddings = tuple(
        sorted(
            chunked,
            key=lambda item: (_metadata_string(item.metadata, "source_path"), item.token_start),
        )
    )
    embedded = embedding_adapter.embed_chunks(chunked_for_embeddings)

    chunk_id_by_signature: dict[tuple[str, int], str] = {
        (
            _metadata_string(chunk.metadata, "source_path"),
            _metadata_int(chunk.metadata, "chunk_index"),
        ): chunk.id
        for chunk in chunks
    }
    chunk_by_signature: dict[tuple[str, int], ChunkRecord] = {
        (
            _metadata_string(chunk.metadata, "source_path"),
            _metadata_int(chunk.metadata, "chunk_index"),
        ): chunk
        for chunk in chunks
    }

    embeddings: list[EmbeddingRecord] = []
    for item in embedded:
        source_path = _metadata_string(item.metadata, "source_path")
        chunk_index = _metadata_int(item.metadata, "chunk_index")
        signature = (source_path, chunk_index)
        if signature not in chunk_id_by_signature:
            continue
        chunk = chunk_by_signature.get(signature)
        if chunk is None:
            continue

        chunk_id = chunk_id_by_signature[signature]
        embedding_id = _sha256(f"{chunk_id}:{model_name}")[:64]
        metadata = dict(item.metadata)
        metadata.setdefault("document_id", chunk.document_id)
        metadata.setdefault("text", chunk.text)
        embeddings.append(
            EmbeddingRecord(
                id=embedding_id,
                chunk_id=chunk_id,
                values=item.values,
                model=model_name,
                metadata=metadata,
            )
        )

    if persist_embeddings_locally:
        embedding_repo.upsert_many(tuple(embeddings))
    vector_adapter.upsert(namespace, tuple(embeddings))

    summary = IngestionSummary(
        processed=len(extraction.extracted),
        skipped=0,
        failed=len(extraction.failures),
        documents=len(documents),
        chunks=len(chunks),
        embeddings=len(embeddings),
    )
    LOGGER.info(
        (
            "ingestion_summary path=%s processed=%d skipped=%d failed=%d "
            "documents=%d chunks=%d embeddings=%d"
        ),
        path,
        summary.processed,
        summary.skipped,
        summary.failed,
        summary.documents,
        summary.chunks,
        summary.embeddings,
    )
    return summary