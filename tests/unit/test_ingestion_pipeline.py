from __future__ import annotations

from pathlib import Path

from fastai.config import IngestionConfig
from fastai.ingestion import ChunkEmbeddingResult, IngestionSummary, ingest_path
from fastai.storage import ChunkRecord, DocumentRecord, EmbeddingRecord


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


class _FakeDocumentRepo:
    def __init__(self) -> None:
        self.items: dict[str, DocumentRecord] = {}

    def upsert(self, document: DocumentRecord) -> DocumentRecord:
        self.items[document.id] = document
        return document

    def get(self, document_id: str) -> DocumentRecord | None:
        return self.items.get(document_id)

    def list_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.items))


class _FakeChunkRepo:
    def __init__(self) -> None:
        self.items: dict[str, ChunkRecord] = {}

    def upsert_many(self, chunks: tuple[ChunkRecord, ...]) -> tuple[ChunkRecord, ...]:
        for chunk in chunks:
            self.items[chunk.id] = chunk
        return chunks

    def list_by_document(self, document_id: str) -> tuple[ChunkRecord, ...]:
        values = [item for item in self.items.values() if item.document_id == document_id]
        values.sort(key=lambda item: item.chunk_index)
        return tuple(values)


class _FakeEmbeddingRepo:
    def __init__(self) -> None:
        self.items: dict[str, EmbeddingRecord] = {}

    def upsert_many(self, embeddings: tuple[EmbeddingRecord, ...]) -> tuple[EmbeddingRecord, ...]:
        for embedding in embeddings:
            self.items[embedding.id] = embedding
        return embeddings

    def list_by_chunk_ids(self, chunk_ids: tuple[str, ...]) -> tuple[EmbeddingRecord, ...]:
        return tuple(item for item in self.items.values() if item.chunk_id in chunk_ids)


class _FakeVectorAdapter:
    def __init__(self) -> None:
        self.namespaces: list[str] = []
        self.embeddings: list[EmbeddingRecord] = []

    def upsert(self, namespace: str, embeddings: tuple[EmbeddingRecord, ...]) -> None:
        self.namespaces.append(namespace)
        self.embeddings.extend(embeddings)

    def query(
        self,
        namespace: str,
        vector: tuple[float, ...],
        *,
        top_k: int,
        min_score: float,
    ) -> tuple:
        return ()

    def delete(self, namespace: str, embedding_ids: tuple[str, ...]) -> int:
        return 0

    def delete_namespace(self, namespace: str) -> int:
        return 0


class _FakeEmbeddingAdapter:
    def embed_texts(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        return tuple((float(index + 1), 0.0, 1.0) for index, _ in enumerate(texts))

    def embed_chunks(self, chunks) -> tuple[ChunkEmbeddingResult, ...]:
        vectors = self.embed_texts(tuple(chunk.text for chunk in chunks))
        return tuple(
            ChunkEmbeddingResult(
                text=chunk.text,
                values=vector,
                metadata=dict(chunk.metadata),
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        )


def test_ingest_path_indexes_txt_and_pdf_end_to_end(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.txt").write_text("alpha beta gamma delta", encoding="utf-8")
    _create_minimal_pdf(docs / "reference.pdf", "policy notes")

    document_repo = _FakeDocumentRepo()
    chunk_repo = _FakeChunkRepo()
    embedding_repo = _FakeEmbeddingRepo()
    vector_adapter = _FakeVectorAdapter()

    summary = ingest_path(
        path=str(docs),
        namespace="default",
        model_name="text-embedding-3-small",
        ingestion_config=IngestionConfig(chunk_size_tokens=3, chunk_overlap_tokens=1),
        document_repo=document_repo,
        chunk_repo=chunk_repo,
        embedding_repo=embedding_repo,
        vector_adapter=vector_adapter,
        embedding_adapter=_FakeEmbeddingAdapter(),
        persist_embeddings_locally=True,
    )

    assert isinstance(summary, IngestionSummary)
    assert summary.processed == 2
    assert summary.failed == 0
    assert summary.documents == 2
    assert summary.chunks > 0
    assert summary.embeddings == summary.chunks
    assert len(document_repo.items) == 2
    assert len(chunk_repo.items) == summary.chunks
    assert len(embedding_repo.items) == summary.embeddings
    assert vector_adapter.namespaces == ["default"]


def test_ingest_path_reports_failed_files_with_continue_policy(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "ok.txt").write_text("alpha beta", encoding="utf-8")
    (docs / "empty.txt").write_text("\n\n\t  ", encoding="utf-8")

    summary = ingest_path(
        path=str(docs),
        namespace="default",
        model_name="text-embedding-3-small",
        ingestion_config=IngestionConfig(failure_policy="continue", chunk_size_tokens=3),
        document_repo=_FakeDocumentRepo(),
        chunk_repo=_FakeChunkRepo(),
        embedding_repo=_FakeEmbeddingRepo(),
        vector_adapter=_FakeVectorAdapter(),
        embedding_adapter=_FakeEmbeddingAdapter(),
        persist_embeddings_locally=True,
    )

    assert summary.processed == 1
    assert summary.failed == 1