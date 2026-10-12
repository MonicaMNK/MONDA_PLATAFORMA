"""Update the server default to current Gemini embedding model.

Revision ID: 20261011_0003
Revises: 20261004_0002
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261011_0003"
down_revision: Union[str, None] = "20261004_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "contenidos",
        "modelo_embedding",
        schema="monda",
        existing_type=sa.String(length=100),
        server_default="gemini-embedding-2",
    )


def downgrade() -> None:
    op.alter_column(
        "contenidos",
        "modelo_embedding",
        schema="monda",
        existing_type=sa.String(length=100),
        server_default="text-embedding-004",
    )
