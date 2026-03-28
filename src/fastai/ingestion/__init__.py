"""Ingestion helpers for path validation and file discovery."""

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

__all__ = [
    "ExtractionBatchResult",
    "ExtractionFailure",
    "ExtractedDocument",
    "IngestionDiscoveryOptions",
    "SUPPORTED_DEDUPE_MODES",
    "SUPPORTED_FAILURE_POLICIES",
    "SUPPORTED_INGESTION_EXTENSIONS",
    "discover_ingestion_files",
    "discover_paths",
    "extract_text_batch",
    "extract_text_from_file",
    "extract_text_from_pdf",
    "extract_text_from_txt",
    "normalize_extracted_text",
    "resolve_ingestion_discovery_options",
    "split_supported_paths",
    "validate_ingestion_path",
]