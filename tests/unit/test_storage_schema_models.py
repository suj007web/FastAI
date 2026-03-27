from __future__ import annotations

from typing import cast

from sqlalchemy import Index, Table
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from fastai.storage import (
    DEFAULT_VECTOR_DIMENSION,
    Base,
    DocumentModel,
    EmbeddingModel,
    RouteDefinitionModel,
)


def test_schema_defines_expected_tables() -> None:
    table_names = set(Base.metadata.tables.keys())

    assert table_names == {
        "documents",
        "chunks",
        "embeddings",
        "route_definitions",
    }


def test_embeddings_table_uses_pgvector_default_dimension() -> None:
    vector_column = EmbeddingModel.__table__.c.vector

    assert getattr(vector_column.type, "dim", None) == DEFAULT_VECTOR_DIMENSION


def test_schema_includes_vector_and_metadata_lookup_indexes() -> None:
    embeddings_table = cast(Table, EmbeddingModel.__table__)
    documents_table = cast(Table, DocumentModel.__table__)
    route_definitions_table = cast(Table, RouteDefinitionModel.__table__)

    embedding_indexes = {str(index.name): index for index in embeddings_table.indexes}
    document_indexes = {str(index.name): index for index in documents_table.indexes}
    route_indexes = {str(index.name): index for index in route_definitions_table.indexes}

    ivfflat_index = embedding_indexes["ix_embeddings_vector_ivfflat"]
    assert isinstance(ivfflat_index, Index)
    assert ivfflat_index.dialect_options["postgresql"]["using"] == "ivfflat"
    assert ivfflat_index.dialect_options["postgresql"]["ops"] == {"vector": "vector_cosine_ops"}
    assert ivfflat_index.dialect_options["postgresql"]["with"] == {"lists": 100}

    assert "ix_documents_source_path" in document_indexes
    assert "ix_route_definitions_route_path" in route_indexes


def test_schema_compiles_to_postgresql_ddl() -> None:
    dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    documents_table = cast(Table, DocumentModel.__table__)
    embeddings_table = cast(Table, EmbeddingModel.__table__)
    documents_sql = str(CreateTable(documents_table).compile(dialect=dialect))
    embeddings_sql = str(CreateTable(embeddings_table).compile(dialect=dialect))

    assert "CREATE TABLE documents" in documents_sql
    assert "CREATE TABLE embeddings" in embeddings_sql
    assert "vector VECTOR(1536)" in embeddings_sql
