from __future__ import annotations

from pathlib import Path

import pytest

from fastai.config import IngestionConfig
from fastai.ingestion import (
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


def test_validate_ingestion_path_rejects_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    with pytest.raises(FileNotFoundError, match="does not exist"):
        validate_ingestion_path(str(missing))


def test_discover_ingestion_files_finds_txt_and_pdf_recursively(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    nested = root / "nested"
    nested.mkdir(parents=True)

    (root / "a.txt").write_text("alpha", encoding="utf-8")
    (nested / "b.PDF").write_text("beta", encoding="utf-8")

    discovered = discover_ingestion_files(str(root))
    discovered_names = tuple(path.name for path in discovered)

    assert SUPPORTED_INGESTION_EXTENSIONS == frozenset({".txt", ".pdf"})
    assert discovered_names == ("a.txt", "b.PDF")


def test_discover_ingestion_files_skips_unsupported_with_warning(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    root = tmp_path / "corpus"
    root.mkdir()
    (root / "ok.txt").write_text("ok", encoding="utf-8")
    (root / "notes.md").write_text("skip", encoding="utf-8")

    with caplog.at_level("WARNING", logger="fastai.ingestion"):
        discovered = discover_ingestion_files(str(root))

    assert tuple(path.name for path in discovered) == ("ok.txt",)
    assert "Skipping unsupported file for ingestion" in caplog.text
    assert "notes.md" in caplog.text


def test_discover_ingestion_files_fail_fast_on_unsupported_file(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    root.mkdir()
    (root / "ok.txt").write_text("ok", encoding="utf-8")
    (root / "notes.md").write_text("skip", encoding="utf-8")

    options = IngestionDiscoveryOptions(
        recursive=True,
        include_globs=(),
        exclude_globs=(),
        max_files=100,
        failure_policy="fail_fast",
        dedupe_mode="checksum_path",
    )

    with pytest.raises(RuntimeError, match="Unsupported file discovered"):
        discover_ingestion_files(str(root), options=options)


def test_discover_paths_non_recursive_only_reads_current_directory(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    nested = root / "nested"
    nested.mkdir(parents=True)
    (root / "top.txt").write_text("top", encoding="utf-8")
    (nested / "child.txt").write_text("child", encoding="utf-8")

    discovered = discover_paths(root, recursive=False)
    assert tuple(path.name for path in discovered) == ("top.txt",)


def test_discover_ingestion_files_respects_include_and_exclude_globs(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    docs = root / "docs"
    archived = docs / "archive"
    archived.mkdir(parents=True)
    (docs / "a.txt").write_text("a", encoding="utf-8")
    (docs / "b.pdf").write_text("b", encoding="utf-8")
    (archived / "c.txt").write_text("c", encoding="utf-8")

    options = IngestionDiscoveryOptions(
        recursive=True,
        include_globs=("docs/*", "docs/**/*.pdf"),
        exclude_globs=("docs/archive/*",),
        max_files=100,
        failure_policy="continue",
        dedupe_mode="checksum_path",
    )

    discovered = discover_ingestion_files(str(root), options=options)
    assert tuple(path.relative_to(root).as_posix() for path in discovered) == (
        "docs/a.txt",
        "docs/b.pdf",
    )


def test_discover_ingestion_files_respects_max_files_continue_policy(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    root.mkdir()
    (root / "a.txt").write_text("a", encoding="utf-8")
    (root / "b.txt").write_text("b", encoding="utf-8")
    (root / "c.pdf").write_text("c", encoding="utf-8")

    options = IngestionDiscoveryOptions(
        recursive=True,
        include_globs=(),
        exclude_globs=(),
        max_files=2,
        failure_policy="continue",
        dedupe_mode="checksum_path",
    )

    discovered = discover_ingestion_files(str(root), options=options)
    assert tuple(path.name for path in discovered) == ("a.txt", "b.txt")


def test_discover_ingestion_files_respects_max_files_fail_fast_policy(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    root.mkdir()
    (root / "a.txt").write_text("a", encoding="utf-8")
    (root / "b.txt").write_text("b", encoding="utf-8")

    options = IngestionDiscoveryOptions(
        recursive=True,
        include_globs=(),
        exclude_globs=(),
        max_files=1,
        failure_policy="fail_fast",
        dedupe_mode="checksum_path",
    )

    with pytest.raises(RuntimeError, match="max_files=1"):
        discover_ingestion_files(str(root), options=options)


def test_discover_ingestion_files_dedupe_checksum_only(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    root.mkdir()
    (root / "a.txt").write_text("same", encoding="utf-8")
    (root / "b.txt").write_text("same", encoding="utf-8")

    options = IngestionDiscoveryOptions(
        recursive=True,
        include_globs=(),
        exclude_globs=(),
        max_files=10,
        failure_policy="continue",
        dedupe_mode="checksum_only",
    )

    discovered = discover_ingestion_files(str(root), options=options)
    assert tuple(path.name for path in discovered) == ("a.txt",)


def test_resolve_ingestion_discovery_options_validates_controls() -> None:
    assert SUPPORTED_FAILURE_POLICIES == frozenset({"continue", "fail_fast"})
    assert SUPPORTED_DEDUPE_MODES == frozenset({"checksum_path", "checksum_only"})

    options = resolve_ingestion_discovery_options()
    assert options.recursive is True
    assert options.max_files == 10000
    assert options.failure_policy == "continue"
    assert options.dedupe_mode == "checksum_path"

    with pytest.raises(ValueError, match="max_files"):
        resolve_ingestion_discovery_options(
            ingestion=IngestionConfig(max_files=0)
        )


def test_split_supported_paths_partitions_by_extension(tmp_path: Path) -> None:
    txt = tmp_path / "good.txt"
    pdf = tmp_path / "good.pdf"
    bad = tmp_path / "bad.csv"
    paths = (txt, pdf, bad)

    supported, unsupported = split_supported_paths(paths)
    assert tuple(path.name for path in supported) == ("good.txt", "good.pdf")
    assert tuple(path.name for path in unsupported) == ("bad.csv",)