"""PI7 base: 20 relational tables.

Revision ID: 20261004_0001
Revises: None
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261004_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLE_VALUES = ("administrador", "docente", "estudiante")

def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS monda")

    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rol", sa.String(20), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("correo", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(100), nullable=False),
        sa.Column("seudonimo", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("estado", sa.String(15), nullable=False, server_default="pendiente"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("rol IN ('administrador','docente','estudiante')", name="ck_usuarios_rol"),
        sa.CheckConstraint("estado IN ('activo','inactivo','pendiente')", name="ck_usuarios_estado"),
        sa.CheckConstraint("version > 0", name="ck_usuarios_version"),
        schema="monda",
    )
    op.create_index("ux_usuarios_correo", "usuarios", [sa.text("lower(correo)")], unique=True, schema="monda")

    op.create_table(
        "cursos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("docente_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("estado", sa.String(12), nullable=False, server_default="activo"),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("estado IN ('activo','archivado')", name="ck_cursos_estado"),
        schema="monda",
    )
    op.create_index("ix_cursos_docente", "cursos", ["docente_id", "estado"], schema="monda")

    op.create_table(
        "matriculas",
        sa.Column("curso_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.cursos.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("estudiante_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("estado", sa.String(12), nullable=False, server_default="activa"),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("estado IN ('activa','inactiva')", name="ck_matriculas_estado"),
        schema="monda",
    )
    op.create_index("ix_matriculas_estudiante", "matriculas", ["estudiante_id", "estado"], schema="monda")

    op.create_table(
        "contenidos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("documento_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("curso_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.cursos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("nombre_original", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("tamano_bytes", sa.BigInteger(), nullable=False),
        sa.Column("s3_key", sa.Text(), nullable=False, unique=True),
        sa.Column("hash_sha256", sa.CHAR(64), nullable=False),
        sa.Column("autor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("estado_indexacion", sa.String(15), nullable=False, server_default="pendiente"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("modelo_embedding", sa.String(100), nullable=False, server_default="text-embedding-004"),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("documento_id", "version", name="uq_contenidos_documento_version"),
        sa.UniqueConstraint("id", "curso_id", name="uq_contenidos_id_curso"),
        sa.CheckConstraint("version > 0", name="ck_contenidos_version"),
        sa.CheckConstraint("tamano_bytes > 0 AND tamano_bytes <= 20971520", name="ck_contenidos_tamano"),
        sa.CheckConstraint("mime_type IN ('application/pdf','application/vnd.openxmlformats-officedocument.wordprocessingml.document')", name="ck_contenidos_mime"),
        sa.CheckConstraint("estado_indexacion IN ('pendiente','procesando','indexado','error')", name="ck_contenidos_indexacion"),
        sa.CheckConstraint("NOT activo OR estado_indexacion = 'indexado'", name="ck_contenidos_activo_indexado"),
        schema="monda",
    )
    op.create_index("ux_contenido_activo", "contenidos", ["documento_id"], unique=True, schema="monda", postgresql_where=sa.text("activo"))
    op.create_index("ix_contenidos_curso", "contenidos", ["curso_id", "estado_indexacion", "activo"], schema="monda")

    op.create_table(
        "conversaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("curso_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.cursos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("estado", sa.String(10), nullable=False, server_default="activa"),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("estado IN ('activa','cerrada')", name="ck_conversaciones_estado"),
        schema="monda",
    )

    op.create_table(
        "mensajes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversacion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.conversaciones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("autor", sa.String(10), nullable=False),
        sa.Column("contenido", sa.Text(), nullable=False),
        sa.Column("fuentes", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("score_max", sa.Float(), nullable=True),
        sa.Column("evidencia_suficiente", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("autor IN ('usuario','tutor')", name="ck_mensajes_autor"),
        sa.CheckConstraint("jsonb_typeof(fuentes) = 'array'", name="ck_mensajes_fuentes"),
        sa.CheckConstraint("score_max IS NULL OR score_max BETWEEN -1 AND 1", name="ck_mensajes_score"),
        schema="monda",
    )
    op.create_index("ix_mensajes_conversacion", "mensajes", ["conversacion_id", "creado_en"], schema="monda")

    op.create_table(
        "valoraciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mensaje_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.mensajes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("util", sa.Boolean(), nullable=False),
        sa.Column("comentario", sa.String(500)),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("mensaje_id", "usuario_id", name="uq_valoraciones_mensaje_usuario"),
        schema="monda",
    )

    op.create_table(
        "evaluaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("curso_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.cursos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("configuracion", postgresql.JSONB(), nullable=False),
        sa.Column("estado", sa.String(12), nullable=False, server_default="borrador"),
        sa.Column("fecha_inicio", sa.DateTime(timezone=True)),
        sa.Column("fecha_fin", sa.DateTime(timezone=True)),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("jsonb_typeof(configuracion) = 'object'", name="ck_evaluaciones_config"),
        sa.CheckConstraint("estado IN ('borrador','publicada','cerrada')", name="ck_evaluaciones_estado"),
        sa.CheckConstraint("version > 0", name="ck_evaluaciones_version"),
        sa.CheckConstraint("fecha_fin IS NULL OR fecha_inicio IS NULL OR fecha_fin > fecha_inicio", name="ck_evaluaciones_fechas"),
        sa.CheckConstraint("estado = 'borrador' OR (fecha_inicio IS NOT NULL AND fecha_fin IS NOT NULL)", name="ck_evaluaciones_publicacion_fechas"),
        schema="monda",
    )
    op.create_index("ix_evaluaciones_curso", "evaluaciones", ["curso_id", "estado"], schema="monda")

    op.create_table(
        "reactivos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("evaluacion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.evaluaciones.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("enunciado", sa.Text(), nullable=False),
        sa.Column("opciones", postgresql.JSONB(), nullable=False),
        sa.Column("clave_correcta", sa.String(10), nullable=False),
        sa.Column("justificacion", sa.Text(), nullable=False),
        sa.Column("nivel_bloom", sa.String(15), nullable=False),
        sa.Column("dificultad", sa.String(8), nullable=False),
        sa.Column("contenido_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.contenidos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("fragmento_id", sa.Text(), nullable=False),
        sa.Column("estado_revision", sa.String(10), nullable=False, server_default="borrador"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("revisado_por", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.id", ondelete="RESTRICT")),
        sa.Column("fecha_revision", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("id", "evaluacion_id", name="uq_reactivos_id_evaluacion"),
        sa.CheckConstraint("jsonb_typeof(opciones) = 'object' AND opciones <> '{}'::jsonb", name="ck_reactivos_opciones"),
        sa.CheckConstraint("opciones ? clave_correcta", name="ck_reactivos_clave"),
        sa.CheckConstraint("nivel_bloom IN ('recordar','comprender','aplicar','analizar','evaluar','crear')", name="ck_reactivos_bloom"),
        sa.CheckConstraint("dificultad IN ('baja','media','alta')", name="ck_reactivos_dificultad"),
        sa.CheckConstraint("estado_revision IN ('borrador','aprobado','rechazado')", name="ck_reactivos_revision"),
        sa.CheckConstraint("version > 0", name="ck_reactivos_version"),
        sa.CheckConstraint("estado_revision <> 'aprobado' OR (revisado_por IS NOT NULL AND fecha_revision IS NOT NULL)", name="ck_reactivos_aprobacion"),
        schema="monda",
    )

    op.create_table(
        "intentos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("evaluacion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.evaluaciones.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("estudiante_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("fecha_inicio", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("fecha_cierre", sa.DateTime(timezone=True)),
        sa.Column("puntaje", sa.Numeric(5, 2)),
        sa.Column("estado", sa.String(10), nullable=False, server_default="abierto"),
        sa.UniqueConstraint("evaluacion_id", "estudiante_id", name="uq_intentos_eval_estudiante"),
        sa.UniqueConstraint("id", "evaluacion_id", name="uq_intentos_id_evaluacion"),
        sa.CheckConstraint("puntaje IS NULL OR puntaje BETWEEN 0 AND 20", name="ck_intentos_puntaje"),
        sa.CheckConstraint("estado IN ('abierto','cerrado')", name="ck_intentos_estado"),
        sa.CheckConstraint("(estado='abierto' AND fecha_cierre IS NULL AND puntaje IS NULL) OR (estado='cerrado' AND fecha_cierre IS NOT NULL AND puntaje IS NOT NULL)", name="ck_intentos_cierre"),
        schema="monda",
    )
    op.create_index("ix_intentos_estudiante", "intentos", ["estudiante_id", "estado"], schema="monda")

    op.create_table(
        "respuestas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("intento_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reactivo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evaluacion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opcion_elegida", sa.String(10)),
        sa.Column("es_correcta", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("intento_id", "reactivo_id", name="uq_respuestas_intento_reactivo"),
        sa.ForeignKeyConstraint(["intento_id", "evaluacion_id"], ["monda.intentos.id", "monda.intentos.evaluacion_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reactivo_id", "evaluacion_id"], ["monda.reactivos.id", "monda.reactivos.evaluacion_id"], ondelete="RESTRICT"),
        schema="monda",
    )

    op.create_table(
        "eventos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_seudonimo", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.seudonimo", ondelete="RESTRICT"), nullable=False),
        sa.Column("curso_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.cursos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="monda",
    )
    op.create_index("ix_eventos_curso_fecha", "eventos", ["curso_id", "creado_en"], schema="monda")

    op.create_table(
        "alertas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("estudiante_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("curso_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.cursos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("regla", sa.String(40), nullable=False),
        sa.Column("evidencia", postgresql.JSONB(), nullable=False),
        sa.Column("estado", sa.String(10), nullable=False, server_default="abierta"),
        sa.Column("revisado_por", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.id", ondelete="RESTRICT")),
        sa.Column("fecha_revision", sa.DateTime(timezone=True)),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("jsonb_typeof(evidencia) = 'object'", name="ck_alertas_evidencia"),
        sa.CheckConstraint("estado IN ('abierta','revisada')", name="ck_alertas_estado"),
        sa.CheckConstraint("estado <> 'revisada' OR (revisado_por IS NOT NULL AND fecha_revision IS NOT NULL)", name="ck_alertas_revision"),
        schema="monda",
    )
    op.create_index("ux_alerta_abierta", "alertas", ["estudiante_id", "curso_id", "regla"], unique=True, schema="monda", postgresql_where=sa.text("estado = 'abierta'"))

    op.create_table(
        "auditoria",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.id", ondelete="RESTRICT")),
        sa.Column("accion", sa.String(60), nullable=False),
        sa.Column("objeto", sa.Text(), nullable=False),
        sa.Column("resultado", sa.String(30), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="monda",
    )
    op.create_index("ix_auditoria_fecha", "auditoria", ["creado_en"], schema="monda")
    op.execute("""
        CREATE OR REPLACE FUNCTION monda.bloquear_mutacion_auditoria()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION 'AUDITORIA es append-only: UPDATE/DELETE no permitidos';
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER auditoria_inmutable
        BEFORE UPDATE OR DELETE ON monda.auditoria
        FOR EACH ROW EXECUTE FUNCTION monda.bloquear_mutacion_auditoria()
    """)

    op.create_table(
        "configuracion",
        sa.Column("clave", sa.String(60), primary_key=True),
        sa.Column("valor", postgresql.JSONB(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("actualizado_por", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("version > 0", name="ck_configuracion_version"),
        schema="monda",
    )

    op.create_table(
        "sesiones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("familia_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.CHAR(64), nullable=False, unique=True),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revocada", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="monda",
    )

    op.create_table(
        "recuperaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.CHAR(64), nullable=False, unique=True),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usado_en", sa.DateTime(timezone=True)),
        schema="monda",
    )

    op.create_table(
        "permisos_rol",
        sa.Column("rol", sa.String(20), primary_key=True),
        sa.Column("permiso", sa.String(80), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint("rol IN ('administrador','docente','estudiante')", name="ck_permisos_rol_rol"),
        sa.CheckConstraint("version > 0", name="ck_permisos_rol_version"),
        schema="monda",
    )

    op.create_table(
        "sincronizaciones",
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("accion_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("payload_hash", sa.CHAR(64), nullable=False),
        sa.Column("resultado", postgresql.JSONB(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="monda",
    )

    op.create_table(
        "trabajos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("curso_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monda.cursos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tipo", sa.String(15), nullable=False),
        sa.Column("estado", sa.String(15), nullable=False, server_default="pendiente"),
        sa.Column("resultado", postgresql.JSONB()),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("tipo IN ('ingesta','generacion')", name="ck_trabajos_tipo"),
        sa.CheckConstraint("estado IN ('pendiente','procesando','completado','error')", name="ck_trabajos_estado"),
        schema="monda",
    )
    op.create_index("ix_trabajos_curso_estado", "trabajos", ["curso_id", "estado"], schema="monda")


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS monda CASCADE")
