"""File discovery and validation utilities for ingestion bootstrap."""

from __future__ import annotations

import logging
from pathlib import Path

LOGGER = logging.getLogger("fastai.ingestion")
SUPPORTED_INGESTION_EXTENSIONS = frozenset({".txt", ".pdf"})


def validate_ingestion_path(path: str) -> Path:
    """Validate and normalize a local ingestion path."""
    normalized = path.strip()
    if not normalized:
        raise ValueError("Ingestion path must not be empty.")

    resolved = Path(normalized).expanduser()
    if not resolved.exists():
        raise FileNotFoundError(f"Ingestion path does not exist: {resolved}")
    if not resolved.is_file() and not resolved.is_dir():
        raise ValueError(f"Ingestion path must be a file or directory: {resolved}")
    return resolved


def discover_paths(path: Path, *, recursive: bool = True) -> tuple[Path, ...]:
    """Discover file paths from a validated file or directory path."""
    if path.is_file():
        return (path,)

    glob = path.rglob if recursive else path.glob
    discovered = tuple(candidate for candidate in glob("*") if candidate.is_file())
    return tuple(sorted(discovered, key=lambda candidate: str(candidate.as_posix()).lower()))


def split_supported_paths(paths: tuple[Path, ...]) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    """Split discovered files into supported and unsupported sets by extension."""
    supported: list[Path] = []
    unsupported: list[Path] = []

    for candidate in paths:
        extension = candidate.suffix.lower()
        if extension in SUPPORTED_INGESTION_EXTENSIONS:
            supported.append(candidate)
        else:
            unsupported.append(candidate)

    return tuple(supported), tuple(unsupported)


def discover_ingestion_files(path: str, *, recursive: bool = True) -> tuple[Path, ...]:
    """Validate input path and return supported files while warning for skipped files."""
    root = validate_ingestion_path(path)
    discovered = discover_paths(root, recursive=recursive)
    supported, unsupported = split_supported_paths(discovered)

    for skipped in unsupported:
        LOGGER.warning("Skipping unsupported file for ingestion: %s", skipped)

    return supported