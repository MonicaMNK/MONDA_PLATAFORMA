from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class LoginIn(StrictModel):
    correo: str
    password: str


class RecoveryIn(StrictModel):
    correo: str


class ResetIn(StrictModel):
    token: str
    password: str = Field(min_length=8, max_length=128)


class ProfilePatch(StrictModel):
    nombre: str = Field(min_length=2, max_length=150)


class CourseIn(StrictModel):
    nombre: str = Field(min_length=2, max_length=150)
    docenteId: UUID | None = None
    descripcion: str = Field(default="", max_length=5000)


class CoursePatch(StrictModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    estado: str | None = None
    docenteId: UUID | None = None
    descripcion: str | None = Field(default=None, max_length=5000)


class EnrollIn(StrictModel):
    estudianteId: str


class EnrollPatch(StrictModel):
    estado: str


class RagIn(StrictModel):
    question: str = Field(min_length=1, max_length=2000)
    conversationId: str | None = None
    folderId: UUID | None = None
    contentIds: list[UUID] | None = Field(default=None, max_length=100)


class FolderIn(StrictModel):
    nombre: str = Field(min_length=1, max_length=100)
    parentId: UUID | None = None


class FolderPatch(StrictModel):
    nombre: str = Field(min_length=1, max_length=100)


class ContentFolderPatch(StrictModel):
    folderId: UUID | None = None


class RatingIn(StrictModel):
    util: bool
    comentario: str | None = Field(default=None, max_length=500)


class GenerateIn(StrictModel):
    tema: str = Field(min_length=2, max_length=300)
    bloom: str = "comprender"
    dificultad: str = "media"
    cantidad: int = Field(default=5, ge=1, le=20)
    tipo: str = "opcion_multiple"


class ReviewIn(StrictModel):
    enunciado: str | None = None
    opciones: dict[str, str] | None = None
    clave: str | None = None
    justificacion: str | None = Field(default=None, min_length=1, max_length=5000)
    estado: str
    version: int = Field(ge=1)


class PublishIn(StrictModel):
    fechaInicio: datetime
    fechaFin: datetime
    version: int = Field(ge=1)


class ResultsPublishIn(StrictModel):
    version: int = Field(ge=1)


class AttemptIn(StrictModel):
    accion: str
    intentoId: str | None = None
    respuestas: dict[str, str | None] | None = None


class AlertPatch(StrictModel):
    estado: str = "revisada"
    comentario: str | None = Field(default=None, max_length=500)


class AdminUserIn(StrictModel):
    correo: str
    nombre: str = Field(min_length=2, max_length=150)
    rol: str
    estado: str = "pendiente"
    password: str | None = Field(default=None, min_length=8, max_length=72)


class AdminUserPatch(StrictModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    correo: str | None = None
    rol: str | None = None
    estado: str | None = None
    version: int = Field(ge=1)


class RolePatch(StrictModel):
    rol: str
    permisos: list[str]
    version: int = Field(ge=1)


class ConfigPatch(StrictModel):
    topK: int = Field(ge=1, le=10)
    umbral: float = Field(ge=0, le=1)
    mode: str = "fallback"
    modelo: str = "gemini-3.8-flash"
    ollamaModel: str = "llama3"
    version: int = Field(ge=1)


class SyncActionIn(StrictModel):
    actionId: str
    tipo: str
    payload: dict[str, Any] = Field(default_factory=dict)
    version: int = Field(default=1, ge=1)


class SyncIn(StrictModel):
    actions: list[SyncActionIn] = Field(min_length=1, max_length=50)
