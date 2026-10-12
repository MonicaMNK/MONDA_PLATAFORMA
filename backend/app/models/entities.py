from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

try:
    from pgvector.sqlalchemy import Vector as PGVector  # type: ignore
except Exception:  # pragma: no cover
    PGVector = None


def uid() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)


class Vector768(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and PGVector is not None:
            return dialect.type_descriptor(PGVector(768))
        return dialect.type_descriptor(JSON())


class Base(DeclarativeBase):
    pass


UUID = Uuid(as_uuid=False)


class User(Base):
    __tablename__ = "usuarios"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    correo: Mapped[str] = mapped_column(String(254), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(100), nullable=False)
    seudonimo: Mapped[str] = mapped_column(UUID, nullable=False, unique=True, default=uid)
    estado: Mapped[str] = mapped_column(String(15), nullable=False, default="pendiente")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Course(Base):
    __tablename__ = "cursos"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    docente_id: Mapped[str] = mapped_column(UUID, ForeignKey("usuarios.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False, default="")
    estado: Mapped[str] = mapped_column(String(12), nullable=False, default="activo")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Enrollment(Base):
    __tablename__ = "matriculas"
    curso_id: Mapped[str] = mapped_column(UUID, ForeignKey("cursos.id"), primary_key=True)
    estudiante_id: Mapped[str] = mapped_column(UUID, ForeignKey("usuarios.id"), primary_key=True)
    estado: Mapped[str] = mapped_column(String(12), nullable=False, default="activa")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Content(Base):
    __tablename__ = "contenidos"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    documento_id: Mapped[str] = mapped_column(UUID, nullable=False)
    curso_id: Mapped[str] = mapped_column(UUID, ForeignKey("cursos.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    nombre_original: Mapped[str] = mapped_column(String(255), nullable=False, default="material")
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False, default="application/pdf")
    tamano_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    s3_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    autor_id: Mapped[str] = mapped_column(UUID, ForeignKey("usuarios.id"), nullable=False)
    estado_indexacion: Mapped[str] = mapped_column(String(15), nullable=False, default="pendiente")
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    modelo_embedding: Mapped[str] = mapped_column(String(100), nullable=False, default="fallback-lexical-v1")
    carpeta_id: Mapped[str | None] = mapped_column(UUID, ForeignKey("carpetas_contenido.id"), nullable=True, index=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint("documento_id", "version", name="uq_documento_version"), UniqueConstraint("id", "curso_id", name="uq_contenido_curso"))


class ContentFolder(Base):
    __tablename__ = "carpetas_contenido"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    curso_id: Mapped[str] = mapped_column(UUID, ForeignKey("cursos.id"), nullable=False, index=True)
    padre_id: Mapped[str | None] = mapped_column(UUID, ForeignKey("carpetas_contenido.id"), nullable=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    creado_por: Mapped[str] = mapped_column(UUID, ForeignKey("usuarios.id"), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Conversation(Base):
    __tablename__ = "conversaciones"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    usuario_id: Mapped[str] = mapped_column(UUID, ForeignKey("usuarios.id"), nullable=False)
    curso_id: Mapped[str] = mapped_column(UUID, ForeignKey("cursos.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(10), nullable=False, default="activa")
    alcance: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Message(Base):
    __tablename__ = "mensajes"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    conversacion_id: Mapped[str] = mapped_column(UUID, ForeignKey("conversaciones.id"), nullable=False)
    autor: Mapped[str] = mapped_column(String(10), nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    fuentes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    score_max: Mapped[float | None] = mapped_column(Float)
    evidencia_suficiente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    correlation_id: Mapped[str] = mapped_column(UUID, nullable=False, default=uid)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Rating(Base):
    __tablename__ = "valoraciones"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    mensaje_id: Mapped[str] = mapped_column(UUID, ForeignKey("mensajes.id"), nullable=False)
    usuario_id: Mapped[str] = mapped_column(UUID, ForeignKey("usuarios.id"), nullable=False)
    util: Mapped[bool] = mapped_column(Boolean, nullable=False)
    comentario: Mapped[str | None] = mapped_column(String(500))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint("mensaje_id", "usuario_id", name="uq_rating"),)


class Assessment(Base):
    __tablename__ = "evaluaciones"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    curso_id: Mapped[str] = mapped_column(UUID, ForeignKey("cursos.id"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    configuracion: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    estado: Mapped[str] = mapped_column(String(12), nullable=False, default="borrador")
    fecha_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Question(Base):
    __tablename__ = "reactivos"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    evaluacion_id: Mapped[str] = mapped_column(UUID, ForeignKey("evaluaciones.id"), nullable=False)
    enunciado: Mapped[str] = mapped_column(Text, nullable=False)
    opciones: Mapped[dict] = mapped_column(JSON, nullable=False)
    clave_correcta: Mapped[str] = mapped_column(String(10), nullable=False)
    justificacion: Mapped[str] = mapped_column(Text, nullable=False)
    nivel_bloom: Mapped[str] = mapped_column(String(15), nullable=False)
    dificultad: Mapped[str] = mapped_column(String(8), nullable=False)
    contenido_id: Mapped[str] = mapped_column(UUID, ForeignKey("contenidos.id"), nullable=False)
    fragmento_id: Mapped[str] = mapped_column(String(80), nullable=False)
    estado_revision: Mapped[str] = mapped_column(String(10), nullable=False, default="borrador")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    revisado_por: Mapped[str | None] = mapped_column(UUID, ForeignKey("usuarios.id"))
    fecha_revision: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("id", "evaluacion_id", name="uq_reactivo_evaluacion"),)


class Attempt(Base):
    __tablename__ = "intentos"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    evaluacion_id: Mapped[str] = mapped_column(UUID, ForeignKey("evaluaciones.id"), nullable=False)
    estudiante_id: Mapped[str] = mapped_column(UUID, ForeignKey("usuarios.id"), nullable=False)
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now)
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    puntaje: Mapped[float | None] = mapped_column(Numeric(5, 2))
    estado: Mapped[str] = mapped_column(String(10), nullable=False, default="abierto")
    __table_args__ = (UniqueConstraint("evaluacion_id", "estudiante_id", name="uq_attempt"), UniqueConstraint("id", "evaluacion_id", name="uq_intento_evaluacion"))


class Answer(Base):
    __tablename__ = "respuestas"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    intento_id: Mapped[str] = mapped_column(UUID, ForeignKey("intentos.id"), nullable=False)
    reactivo_id: Mapped[str] = mapped_column(UUID, ForeignKey("reactivos.id"), nullable=False)
    evaluacion_id: Mapped[str] = mapped_column(UUID, ForeignKey("evaluaciones.id"), nullable=False)
    opcion_elegida: Mapped[str | None] = mapped_column(String(10))
    es_correcta: Mapped[bool] = mapped_column(Boolean, nullable=False)
    __table_args__ = (UniqueConstraint("intento_id", "reactivo_id", name="uq_answer"),)


class Event(Base):
    __tablename__ = "eventos"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    usuario_seudonimo: Mapped[str] = mapped_column(UUID, nullable=False)
    curso_id: Mapped[str] = mapped_column(UUID, ForeignKey("cursos.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    correlation_id: Mapped[str] = mapped_column(UUID, nullable=False, default=uid)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Alert(Base):
    __tablename__ = "alertas"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    estudiante_id: Mapped[str] = mapped_column(UUID, ForeignKey("usuarios.id"), nullable=False)
    curso_id: Mapped[str] = mapped_column(UUID, ForeignKey("cursos.id"), nullable=False)
    regla: Mapped[str] = mapped_column(String(40), nullable=False)
    evidencia: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    estado: Mapped[str] = mapped_column(String(10), nullable=False, default="abierta")
    revisado_por: Mapped[str | None] = mapped_column(UUID, ForeignKey("usuarios.id"))
    fecha_revision: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Audit(Base):
    __tablename__ = "auditoria"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    actor_id: Mapped[str | None] = mapped_column(UUID, ForeignKey("usuarios.id"))
    accion: Mapped[str] = mapped_column(String(60), nullable=False)
    objeto: Mapped[str] = mapped_column(Text, nullable=False)
    resultado: Mapped[str] = mapped_column(String(30), nullable=False)
    correlation_id: Mapped[str] = mapped_column(UUID, nullable=False, default=uid)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Config(Base):
    __tablename__ = "configuracion"
    clave: Mapped[str] = mapped_column(String(60), primary_key=True)
    valor: Mapped[dict] = mapped_column(JSON, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    actualizado_por: Mapped[str] = mapped_column(UUID, ForeignKey("usuarios.id"), nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class SessionToken(Base):
    __tablename__ = "sesiones"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    usuario_id: Mapped[str] = mapped_column(UUID, ForeignKey("usuarios.id"), nullable=False)
    familia_id: Mapped[str] = mapped_column(UUID, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revocada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Recovery(Base):
    __tablename__ = "recuperaciones"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    usuario_id: Mapped[str] = mapped_column(UUID, ForeignKey("usuarios.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RolePermission(Base):
    __tablename__ = "permisos_rol"
    rol: Mapped[str] = mapped_column(String(20), primary_key=True)
    permiso: Mapped[str] = mapped_column(String(80), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class SyncAction(Base):
    __tablename__ = "sincronizaciones"
    usuario_id: Mapped[str] = mapped_column(UUID, ForeignKey("usuarios.id"), primary_key=True)
    accion_id: Mapped[str] = mapped_column(UUID, primary_key=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    resultado: Mapped[dict] = mapped_column(JSON, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Job(Base):
    __tablename__ = "trabajos"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    usuario_id: Mapped[str] = mapped_column(UUID, ForeignKey("usuarios.id"), nullable=False)
    curso_id: Mapped[str] = mapped_column(UUID, ForeignKey("cursos.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(15), nullable=False)
    estado: Mapped[str] = mapped_column(String(15), nullable=False, default="pendiente")
    resultado: Mapped[dict | None] = mapped_column(JSON)
    correlation_id: Mapped[str] = mapped_column(UUID, nullable=False, default=uid)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class RAGFragment(Base):
    __tablename__ = "fragmentos_rag"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    contenido_id: Mapped[str] = mapped_column(UUID, ForeignKey("contenidos.id"), nullable=False, index=True)
    curso_id: Mapped[str] = mapped_column(UUID, ForeignKey("cursos.id"), nullable=False, index=True)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    ubicacion: Mapped[str | None] = mapped_column(String(255))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(Vector768())
    embedding_model: Mapped[str | None] = mapped_column(String(100))
    embedding_provider: Mapped[str | None] = mapped_column(String(20))
    hash_fragmento: Mapped[str] = mapped_column(String(64), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint("contenido_id", "ordinal", name="uq_frag_ordinal"), UniqueConstraint("contenido_id", "hash_fragmento", name="uq_frag_hash"))


class Draft(Base):
    __tablename__ = "borradores_sync"
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uid)
    usuario_id: Mapped[str] = mapped_column(UUID, ForeignKey("usuarios.id"), nullable=False)
    curso_id: Mapped[str | None] = mapped_column(UUID, ForeignKey("cursos.id"))
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    base_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    accion_id: Mapped[str | None] = mapped_column(UUID)
    sincronizado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint("usuario_id", "accion_id", name="uq_borrador_action"),)
