"""File discovery and validation utilities for ingestion bootstrap."""

from __future__ import annotations

import fnmatch
import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

from fastai.config.defaults import BUILTIN_INGESTION
from fastai.config.types import IngestionConfig

LOGGER = logging.getLogger("fastai.ingestion")
SUPPORTED_INGESTION_EXTENSIONS = frozenset({".txt", ".pdf"})
SUPPORTED_FAILURE_POLICIES = frozenset({"continue", "fail_fast"})
SUPPORTED_DEDUPE_MODES = frozenset({"checksum_path", "checksum_only"})


@dataclass(frozen=True)
class IngestionDiscoveryOptions:
    """Resolved discovery controls for deterministic ingestion file selection."""

    recursive: bool
    include_globs: tuple[str, ...]
    exclude_globs: tuple[str, ...]
    max_files: int
    failure_policy: str
    dedupe_mode: str


def _normalize_globs(value: tuple[str, ...] | None) -> tuple[str, ...]:
    if value is None:
        return ()
    normalized = tuple(item.strip() for item in value if item.strip())
    return tuple(dict.fromkeys(normalized))


def _normalize_failure_policy(value: str | None) -> str:
    candidate = (value or BUILTIN_INGESTION.failure_policy or "continue").strip().lower()
    if candidate not in SUPPORTED_FAILURE_POLICIES:
        raise ValueError(
            "Unsupported ingestion failure_policy. Expected one of "
            f"{sorted(SUPPORTED_FAILURE_POLICIES)}; received '{candidate}'."
        )
    return candidate


def _normalize_dedupe_mode(value: str | None) -> str:
    candidate = (value or BUILTIN_INGESTION.dedupe_mode or "checksum_path").strip().lower()
    if candidate not in SUPPORTED_DEDUPE_MODES:
        raise ValueError(
            "Unsupported ingestion dedupe_mode. Expected one of "
            f"{sorted(SUPPORTED_DEDUPE_MODES)}; received '{candidate}'."
        )
    return candidate


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _matches_globs(relative_path: str, globs: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(relative_path, pattern) for pattern in globs)


def _to_relative_path(root: Path, candidate: Path) -> str:
    if root.is_file():
        return candidate.name
    return candidate.relative_to(root).as_posix()


def resolve_ingestion_discovery_options(
    ingestion: IngestionConfig | None = None,
) -> IngestionDiscoveryOptions:
    """Resolve and validate ingestion controls for file discovery."""
    cfg = ingestion or IngestionConfig()
    recursive = (
        cfg.recursive if cfg.recursive is not None else bool(BUILTIN_INGESTION.recursive)
    )
    max_files = (
        cfg.max_files
        if cfg.max_files is not None
        else int(BUILTIN_INGESTION.max_files or 0)
    )
    if max_files <= 0:
        raise ValueError("Ingestion max_files must be greater than zero.")

    return IngestionDiscoveryOptions(
        recursive=recursive,
        include_globs=_normalize_globs(cfg.include_globs or BUILTIN_INGESTION.include_globs),
        exclude_globs=_normalize_globs(cfg.exclude_globs or BUILTIN_INGESTION.exclude_globs),
        max_files=max_files,
        failure_policy=_normalize_failure_policy(cfg.failure_policy),
        dedupe_mode=_normalize_dedupe_mode(cfg.dedupe_mode),
    )


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


def _apply_glob_filters(
    root: Path,
    discovered: tuple[Path, ...],
    options: IngestionDiscoveryOptions,
) -> tuple[Path, ...]:
    filtered: list[Path] = []
    for candidate in discovered:
        relative = _to_relative_path(root, candidate)
        if options.include_globs and not _matches_globs(relative, options.include_globs):
            continue
        if options.exclude_globs and _matches_globs(relative, options.exclude_globs):
            continue
        filtered.append(candidate)
    return tuple(filtered)


def _apply_dedupe(
    files: tuple[Path, ...],
    options: IngestionDiscoveryOptions,
) -> tuple[Path, ...]:
    if options.dedupe_mode == "checksum_path":
        seen_paths: set[str] = set()
        deduped: list[Path] = []
        for candidate in files:
            key = str(candidate.resolve())
            if key in seen_paths:
                LOGGER.warning("Skipping duplicate path during ingestion discovery: %s", candidate)
                continue
            seen_paths.add(key)
            deduped.append(candidate)
        return tuple(deduped)

    seen_checksums: set[str] = set()
    deduped_by_checksum: list[Path] = []
    for candidate in files:
        checksum = _file_sha256(candidate)
        if checksum in seen_checksums:
            LOGGER.warning(
                "Skipping duplicate file content during ingestion discovery: %s",
                candidate,
            )
            continue
        seen_checksums.add(checksum)
        deduped_by_checksum.append(candidate)

    return tuple(deduped_by_checksum)


def _enforce_max_files(
    files: tuple[Path, ...],
    options: IngestionDiscoveryOptions,
) -> tuple[Path, ...]:
    if len(files) <= options.max_files:
        return files

    message = (
        "Discovered "
        f"{len(files)} supported ingestion files but max_files={options.max_files}."
    )
    if options.failure_policy == "fail_fast":
        raise RuntimeError(message)

    LOGGER.warning("%s Truncating to first %d files.", message, options.max_files)
    return files[: options.max_files]


def discover_ingestion_files(
    path: str,
    *,
    options: IngestionDiscoveryOptions | None = None,
) -> tuple[Path, ...]:
    """Validate input path and return supported files while warning for skipped files."""
    resolved_options = options or resolve_ingestion_discovery_options()
    root = validate_ingestion_path(path)
    discovered = discover_paths(root, recursive=resolved_options.recursive)
    discovered = _apply_glob_filters(root, discovered, resolved_options)
    supported, unsupported = split_supported_paths(discovered)

    for skipped in unsupported:
        if resolved_options.failure_policy == "fail_fast":
            raise RuntimeError(f"Unsupported file discovered for ingestion: {skipped}")
        LOGGER.warning("Skipping unsupported file for ingestion: %s", skipped)

    deduped = _apply_dedupe(supported, resolved_options)
    return _enforce_max_files(deduped, resolved_options)