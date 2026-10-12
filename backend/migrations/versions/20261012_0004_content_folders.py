"""Carpetas jerárquicas de materiales por curso."""
from alembic import op
import sqlalchemy as sa

revision = "20261012_0004"
down_revision = "20261011_0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('carpetas_contenido',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('curso_id', sa.Uuid(), sa.ForeignKey('monda.cursos.id'), nullable=False),
        sa.Column('padre_id', sa.Uuid(), sa.ForeignKey('monda.carpetas_contenido.id')),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('creado_por', sa.Uuid(), sa.ForeignKey('monda.usuarios.id'), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='monda')
    op.create_index('ix_carpetas_curso', 'carpetas_contenido', ['curso_id'], schema='monda')
    op.add_column('contenidos', sa.Column('carpeta_id', sa.Uuid(), nullable=True), schema='monda')
    op.create_foreign_key('fk_contenido_carpeta', 'contenidos', 'carpetas_contenido', ['carpeta_id'], ['id'], source_schema='monda', referent_schema='monda')
    op.create_index('ix_contenidos_carpeta_id', 'contenidos', ['carpeta_id'], schema='monda')
    op.execute("INSERT INTO monda.permisos_rol (rol, permiso, version) VALUES ('administrador', 'rag:query', 1) ON CONFLICT (rol, permiso) DO NOTHING")


def downgrade():
    op.drop_index('ix_contenidos_carpeta_id', table_name='contenidos', schema='monda')
    op.drop_constraint('fk_contenido_carpeta', 'contenidos', schema='monda', type_='foreignkey')
    op.drop_column('contenidos', 'carpeta_id', schema='monda')
    op.drop_table('carpetas_contenido', schema='monda')
