"""Descripción del curso."""
from alembic import op
import sqlalchemy as sa
revision='20261012_0005'
down_revision='20261012_0004'
branch_labels=None
depends_on=None
def upgrade():
    op.add_column('cursos',sa.Column('descripcion',sa.Text(),nullable=False,server_default=''),schema='monda')
    op.add_column('conversaciones',sa.Column('alcance',sa.JSON(),nullable=False,server_default='{}'),schema='monda')
def downgrade():
    op.drop_column('conversaciones','alcance',schema='monda')
    op.drop_column('cursos','descripcion',schema='monda')
