from __future__ import annotations
from datetime import datetime, timezone

from ..models import Content, Course, Question, User


def dtiso(value):
    if isinstance(value,datetime) and value.tzinfo is None:
        value=value.replace(tzinfo=timezone.utc)
    return value.isoformat() if value else None


def user_json(user: User) -> dict:
    return {"id": user.id, "nombre": user.nombre, "correo": user.correo, "rol": user.rol, "estado": user.estado, "version": user.version, "creadoEn": dtiso(user.creado_en)}


def course_json(course: Course) -> dict:
    return {"id": course.id, "courseId": course.id, "nombre": course.nombre, "descripcion": course.descripcion, "estado": course.estado, "docenteId": course.docente_id, "creadoEn": dtiso(course.creado_en)}


def content_json(content: Content) -> dict:
    return {"id": content.id, "contentId": content.id, "documentoId": content.documento_id, "cursoId": content.curso_id, "folderId": content.carpeta_id, "version": content.version, "nombre": content.nombre_original, "mimeType": content.mime_type, "tamanoBytes": content.tamano_bytes, "estado": content.estado_indexacion, "activo": content.activo, "modeloEmbedding": content.modelo_embedding, "creadoEn": dtiso(content.creado_en)}


def question_json(question: Question, include_keys: bool) -> dict:
    data = {
        "id": question.id,
        "questionId": question.id,
        "enunciado": question.enunciado,
        "opciones": question.opciones,
        "nivelBloom": question.nivel_bloom,
        "dificultad": question.dificultad,
        "contenidoId": question.contenido_id,
        "fragmentoId": question.fragmento_id,
        "estadoRevision": question.estado_revision,
        "version": question.version,
    }
    if include_keys:
        data["clave"] = question.clave_correcta
        data["justificacion"] = question.justificacion
    return data
