"""RAG pgvector and offline drafts: tables 21-22.

Revision ID: 20261004_0002
Revises: 20261004_0001
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

class Vector768(sa.types.UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kw) -> str:
        return "vector(768)"


revision: str = "20261004_0002"
down_revision: Union[str, None] = "20261004_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "fragmentos_rag",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("contenido_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("curso_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("ubicacion", sa.String(255)),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("embedding", Vector768()),
        sa.Column("embedding_model", sa.String(100)),
        sa.Column("embedding_provider", sa.String(20)),
        sa.Column("hash_fragmento", sa.CHAR(64), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("contenido_id", "ordinal", name="uq_fragmentos_rag_contenido_ordinal"),
        sa.UniqueConstraint("contenido_id", "hash_fragmento", name="uq_fragmentos_rag_contenido_hash"),
        sa.ForeignKeyConstraint(["contenido_id", "curso_id"], ["monda.contenidos.id", "monda.contenidos.curso_id"], ondelete="CASCADE"),
        sa.CheckConstraint("ordinal >= 0", name="ck_fragmentos_rag_ordinal"),
        sa.CheckConstraint("jsonb_typeof(metadata) = 'object'", name="ck_fragmentos_rag_metadata"),
        sa.CheckConstraint("embedding_provider IS NULL OR embedding_provider IN ('gemini','ollama','fallback')", name="ck_fragmentos_rag_provider"),
        schema="monda",
    )
    op.create_index("ix_fragmentos_rag_curso", "fragmentos_rag", ["curso_id", "contenido_id"], schema="monda")
    op.execute("CREATE INDEX ix_fragmentos_rag_fts ON monda.fragmentos_rag USING gin (to_tsvector('spanish', texto))")
    op.execute("CREATE INDEX ix_fragmentos_rag_vector_hnsw ON monda.fragmentos_rag USING hnsw (embedding vector_cosine_ops) WHERE embedding IS NOT NULL")

    op.create_table(
        "borradores_sync",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("curso_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.cursos.id", ondelete="CASCADE")),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("base_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("accion_id", postgresql.UUID(as_uuid=True)),
        sa.Column("sincronizado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("usuario_id", "accion_id", name="uq_borradores_sync_usuario_accion"),
        sa.CheckConstraint("tipo IN ('borrador_personal','valoracion')", name="ck_borradores_sync_tipo"),
        sa.CheckConstraint("jsonb_typeof(payload) = 'object'", name="ck_borradores_sync_payload"),
        sa.CheckConstraint("base_version > 0", name="ck_borradores_sync_version"),
        schema="monda",
    )
    op.create_index("ix_borradores_sync_usuario", "borradores_sync", ["usuario_id", "sincronizado", "actualizado_en"], schema="monda")


def downgrade() -> None:
    op.drop_table("borradores_sync", schema="monda")
    op.drop_table("fragmentos_rag", schema="monda")
