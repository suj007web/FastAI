"""Ingestion helpers for path validation and file discovery."""

from .chunking import (
    ChunkedText,
    ChunkingOptions,
    chunk_extracted_documents,
    chunk_text,
    resolve_chunking_options,
)
from .discovery import (
    SUPPORTED_DEDUPE_MODES,
    SUPPORTED_FAILURE_POLICIES,
    SUPPORTED_INGESTION_EXTENSIONS,
    IngestionDiscoveryOptions,
    discover_ingestion_files,
    discover_paths,
    resolve_ingestion_discovery_options,
    split_supported_paths,
    validate_ingestion_path,
)
from .embeddings import (
    ChunkEmbeddingResult,
    EmbeddingAdapter,
    LiteLLMEmbeddingAdapter,
    create_embedding_adapter,
)
from .extraction import (
    ExtractedDocument,
    ExtractionBatchResult,
    ExtractionFailure,
    extract_text_batch,
    extract_text_from_file,
    extract_text_from_pdf,
    extract_text_from_txt,
    normalize_extracted_text,
)
from .pipeline import IngestionSummary, ingest_path

__all__ = [
    "ChunkedText",
    "ChunkEmbeddingResult",
    "ChunkingOptions",
    "EmbeddingAdapter",
    "ExtractionBatchResult",
    "ExtractionFailure",
    "ExtractedDocument",
    "LiteLLMEmbeddingAdapter",
    "IngestionDiscoveryOptions",
    "IngestionSummary",
    "SUPPORTED_DEDUPE_MODES",
    "SUPPORTED_FAILURE_POLICIES",
    "SUPPORTED_INGESTION_EXTENSIONS",
    "chunk_extracted_documents",
    "chunk_text",
    "discover_ingestion_files",
    "discover_paths",
    "create_embedding_adapter",
    "extract_text_batch",
    "extract_text_from_file",
    "extract_text_from_pdf",
    "extract_text_from_txt",
    "ingest_path",
    "normalize_extracted_text",
    "resolve_chunking_options",
    "resolve_ingestion_discovery_options",
    "split_supported_paths",
    "validate_ingestion_path",
]