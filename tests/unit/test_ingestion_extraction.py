from __future__ import annotations

from pathlib import Path

import pytest

from fastai.ingestion import (
    extract_text_batch,
    extract_text_from_file,
    extract_text_from_pdf,
    extract_text_from_txt,
    normalize_extracted_text,
)


def _create_minimal_pdf(path: Path, text: str) -> None:
    safe_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT\n/F1 18 Tf\n72 100 Td\n({safe_text}) Tj\nET\n".encode("latin-1")

    objects = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        3: (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        ),
        4: (
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"endstream"
        ),
        5: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }

    chunks: list[bytes] = [b"%PDF-1.4\n"]
    offsets: dict[int, int] = {}

    for number in range(1, 6):
        offsets[number] = sum(len(chunk) for chunk in chunks)
        chunks.append(f"{number} 0 obj\n".encode("ascii"))
        chunks.append(objects[number])
        chunks.append(b"\nendobj\n")

    xref_offset = sum(len(chunk) for chunk in chunks)
    chunks.append(b"xref\n0 6\n")
    chunks.append(b"0000000000 65535 f \n")
    for number in range(1, 6):
        chunks.append(f"{offsets[number]:010d} 00000 n \n".encode("ascii"))
    chunks.append(b"trailer\n<< /Size 6 /Root 1 0 R >>\n")
    chunks.append(b"startxref\n")
    chunks.append(f"{xref_offset}\n".encode("ascii"))
    chunks.append(b"%%EOF\n")

    path.write_bytes(b"".join(chunks))


def test_normalize_extracted_text_stabilizes_whitespace() -> None:
    raw = "  hello\t\tworld\r\n\r\n\r\nnext\vline  "
    assert normalize_extracted_text(raw) == "hello world\n\nnext line"


def test_extract_text_from_txt_handles_bom_and_non_empty_content(tmp_path: Path) -> None:
    source = tmp_path / "doc.txt"
    source.write_text("\ufeff  Hello\tworld\n\n", encoding="utf-8")

    extracted = extract_text_from_txt(source)
    assert extracted == "Hello world"


def test_extract_text_from_pdf_uses_pypdf(tmp_path: Path) -> None:
    source = tmp_path / "doc.pdf"
    _create_minimal_pdf(source, "Hello PDF")

    extracted = extract_text_from_pdf(source)
    assert "Hello PDF" in extracted


def test_extract_text_from_file_rejects_unsupported_extension(tmp_path: Path) -> None:
    source = tmp_path / "doc.csv"
    source.write_text("a,b", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file extension"):
        extract_text_from_file(source)


def test_extract_text_batch_continue_isolates_failures(tmp_path: Path) -> None:
    good_txt = tmp_path / "a.txt"
    good_pdf = tmp_path / "b.pdf"
    bad_csv = tmp_path / "c.csv"
    good_txt.write_text("alpha", encoding="utf-8")
    _create_minimal_pdf(good_pdf, "beta")
    bad_csv.write_text("x,y", encoding="utf-8")

    result = extract_text_batch((good_txt, bad_csv, good_pdf), failure_policy="continue")

    assert tuple(item.path.name for item in result.extracted) == ("a.txt", "b.pdf")
    assert tuple(item.path.name for item in result.failures) == ("c.csv",)


def test_extract_text_batch_fail_fast_raises_on_first_error(tmp_path: Path) -> None:
    good_txt = tmp_path / "a.txt"
    bad_csv = tmp_path / "c.csv"
    good_txt.write_text("alpha", encoding="utf-8")
    bad_csv.write_text("x,y", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file extension"):
        extract_text_batch((good_txt, bad_csv), failure_policy="fail_fast")