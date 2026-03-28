from __future__ import annotations

from pathlib import Path

import pytest

from fastai.ingestion import (
    SUPPORTED_INGESTION_EXTENSIONS,
    discover_ingestion_files,
    discover_paths,
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


def test_discover_paths_non_recursive_only_reads_current_directory(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    nested = root / "nested"
    nested.mkdir(parents=True)
    (root / "top.txt").write_text("top", encoding="utf-8")
    (nested / "child.txt").write_text("child", encoding="utf-8")

    discovered = discover_paths(root, recursive=False)
    assert tuple(path.name for path in discovered) == ("top.txt",)


def test_split_supported_paths_partitions_by_extension(tmp_path: Path) -> None:
    txt = tmp_path / "good.txt"
    pdf = tmp_path / "good.pdf"
    bad = tmp_path / "bad.csv"
    paths = (txt, pdf, bad)

    supported, unsupported = split_supported_paths(paths)
    assert tuple(path.name for path in supported) == ("good.txt", "good.pdf")
    assert tuple(path.name for path in unsupported) == ("bad.csv",)