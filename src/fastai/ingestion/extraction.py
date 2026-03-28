"""Text extraction utilities for ingestion pipeline inputs."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .discovery import SUPPORTED_FAILURE_POLICIES

LOGGER = logging.getLogger("fastai.ingestion")
_WHITESPACE_RE = re.compile(r"[\t\f\v ]+")
_NEWLINE_RE = re.compile(r"\n{3,}")


@dataclass(frozen=True)
class ExtractedDocument:
    """Normalized text payload extracted from a source file."""

    path: Path
    text: str


@dataclass(frozen=True)
class ExtractionFailure:
    """Failure details for one source file during extraction."""

    path: Path
    reason: str


@dataclass(frozen=True)
class ExtractionBatchResult:
    """Batch extraction result with isolated failures per source file."""

    extracted: tuple[ExtractedDocument, ...]
    failures: tuple[ExtractionFailure, ...]


def normalize_extracted_text(text: str) -> str:
    """Normalize text to stable whitespace for downstream chunking."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = _WHITESPACE_RE.sub(" ", normalized)
    normalized = _NEWLINE_RE.sub("\n\n", normalized)
    lines = tuple(line.strip() for line in normalized.split("\n"))
    return "\n".join(lines).strip()


def extract_text_from_txt(path: Path) -> str:
    """Extract and normalize text from a UTF-compatible text file."""
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    normalized = normalize_extracted_text(raw)
    if not normalized:
        raise ValueError(f"Extracted text is empty for file: {path}")
    return normalized


def _load_pdf_reader(path: Path) -> Any:
    from pypdf import PdfReader

    return PdfReader(str(path))


def extract_text_from_pdf(path: Path) -> str:
    """Extract and normalize text from a PDF file using pypdf."""
    reader = _load_pdf_reader(path)
    parts: list[str] = []
    for page in reader.pages:
        extracted = page.extract_text() or ""
        if extracted:
            parts.append(extracted)

    normalized = normalize_extracted_text("\n\n".join(parts))
    if not normalized:
        raise ValueError(f"Extracted text is empty for file: {path}")
    return normalized


def extract_text_from_file(path: Path) -> str:
    """Extract normalized text from a supported source file."""
    extension = path.suffix.lower()
    if extension == ".txt":
        return extract_text_from_txt(path)
    if extension == ".pdf":
        return extract_text_from_pdf(path)
    raise ValueError(f"Unsupported file extension for extraction: {extension}")


def extract_text_batch(
    paths: tuple[Path, ...],
    *,
    failure_policy: str = "continue",
) -> ExtractionBatchResult:
    """Extract text from multiple files with per-file failure isolation."""
    policy = failure_policy.strip().lower()
    if policy not in SUPPORTED_FAILURE_POLICIES:
        raise ValueError(
            "Unsupported extraction failure policy. Expected one of "
            f"{sorted(SUPPORTED_FAILURE_POLICIES)}; received '{policy}'."
        )

    extracted: list[ExtractedDocument] = []
    failures: list[ExtractionFailure] = []

    for path in paths:
        try:
            extracted_text = extract_text_from_file(path)
            extracted.append(ExtractedDocument(path=path, text=extracted_text))
        except Exception as exc:
            if policy == "fail_fast":
                raise
            LOGGER.warning("Extraction failed for '%s': %s", path, exc)
            failures.append(ExtractionFailure(path=path, reason=str(exc)))

    return ExtractionBatchResult(extracted=tuple(extracted), failures=tuple(failures))