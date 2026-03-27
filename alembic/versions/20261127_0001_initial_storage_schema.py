"""Initial storage schema for documents, chunks, embeddings, and route definitions.

Revision ID: 20261127_0001
Revises:
Create Date: 2026-11-27 00:00:00
"""

from __future__ import annotations

import pgvector.sqlalchemy
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20261127_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("source_path", sa.String(length=1024), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("checksum"),
    )
    op.create_index("ix_documents_created_at", "documents", ["created_at"], unique=False)
    op.create_index("ix_documents_source_path", "documents", ["source_path"], unique=False)

    op.create_table(
        "chunks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_chunks_document_chunk_index"),
    )
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"], unique=False)

    op.create_table(
        "embeddings",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("chunk_id", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=256), nullable=False),
        sa.Column("vector", pgvector.sqlalchemy.Vector(dim=1536), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["chunk_id"], ["chunks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_embeddings_chunk_id", "embeddings", ["chunk_id"], unique=False)
    op.create_index("ix_embeddings_model", "embeddings", ["model"], unique=False)
    op.create_index(
        "ix_embeddings_vector_ivfflat",
        "embeddings",
        ["vector"],
        unique=False,
        postgresql_using="ivfflat",
        postgresql_ops={"vector": "vector_cosine_ops"},
        postgresql_with={"lists": 100},
    )

    op.create_table(
        "route_definitions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("route_name", sa.String(length=128), nullable=False),
        sa.Column("route_path", sa.String(length=256), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("retrieval_top_k", sa.Integer(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("route_name"),
        sa.UniqueConstraint("route_path"),
    )
    op.create_index(
        "ix_route_definitions_route_name",
        "route_definitions",
        ["route_name"],
        unique=False,
    )
    op.create_index(
        "ix_route_definitions_route_path",
        "route_definitions",
        ["route_path"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_route_definitions_route_path", table_name="route_definitions")
    op.drop_index("ix_route_definitions_route_name", table_name="route_definitions")
    op.drop_table("route_definitions")

    op.drop_index("ix_embeddings_vector_ivfflat", table_name="embeddings")
    op.drop_index("ix_embeddings_model", table_name="embeddings")
    op.drop_index("ix_embeddings_chunk_id", table_name="embeddings")
    op.drop_table("embeddings")

    op.drop_index("ix_chunks_document_id", table_name="chunks")
    op.drop_table("chunks")

    op.drop_index("ix_documents_source_path", table_name="documents")
    op.drop_index("ix_documents_created_at", table_name="documents")
    op.drop_table("documents")
