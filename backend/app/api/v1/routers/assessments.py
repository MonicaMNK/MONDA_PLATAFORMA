from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from ...deps import current_user
from ....core.errors import api_error
from ....db.audit import audit
from ....db.session import get_db
from ....models import Answer, Assessment, Attempt, Event, Question, User, uid
from ....schemas import AttemptIn, GenerateIn, PublishIn, ReviewIn
from ....services.access import can_access_course, require_permission, teacher_course
from ....services.assessment_service import generate_assessment, publish_assessment
from ....services.serializers import dtiso, question_json

router = APIRouter(prefix="/api", tags=["Evaluaciones"])


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


@router.post("/courses/{courseId}/assessments/generate", status_code=202)
def generate(courseId: str, body: GenerateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return generate_assessment(db, user, courseId, body.tema, body.bloom, body.dificultad, body.cantidad, body.tipo)


@router.get("/courses/{courseId}/assessments")
def list_assessments(courseId: str, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), user: User = Depends(current_user), db: Session = Depends(get_db)):
    can_access_course(db, user, courseId)
    q = db.query(Assessment).filter(Assessment.curso_id == courseId)
    if user.rol == "estudiante":
        q = q.filter(Assessment.estado.in_(["publicada", "cerrada"]))
    total = q.count()
    rows = q.order_by(Assessment.creado_en.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"items": [{"id": a.id, "titulo": a.titulo, "estado": a.estado, "fechaInicio": dtiso(a.fecha_inicio), "fechaFin": dtiso(a.fecha_fin), "version": a.version} for a in rows], "page": page, "total": total}


@router.get("/assessments/{id}")
def assessment_detail(id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    assessment = db.get(Assessment, id)
    if not assessment:
        api_error(404, "ASSESSMENT_NOT_FOUND", "Evaluación no encontrada.")
    can_access_course(db, user, assessment.curso_id)
    if user.rol == "estudiante" and assessment.estado == "borrador":
        api_error(403, "FORBIDDEN", "La evaluación todavía no está publicada.")
    include_keys = user.rol in {"docente", "administrador"}
    questions = db.query(Question).filter(Question.evaluacion_id == assessment.id).order_by(Question.id).all()
    return {"id": assessment.id, "cursoId": assessment.curso_id, "titulo": assessment.titulo, "estado": assessment.estado, "configuracion": assessment.configuracion, "fechaInicio": dtiso(assessment.fecha_inicio), "fechaFin": dtiso(assessment.fecha_fin), "version": assessment.version, "questions": [question_json(q, include_keys) for q in questions]}


@router.patch("/questions/{questionId}/review")
def review_question(questionId: str, body: ReviewIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    question = db.get(Question, questionId)
    if not question:
        api_error(404, "QUESTION_NOT_FOUND", "Reactivo no encontrado.")
    assessment = db.get(Assessment, question.evaluacion_id)
    teacher_course(db, user, assessment.curso_id)
    if assessment.estado != "borrador":
        api_error(409, "ASSESSMENT_IMMUTABLE", "Una evaluación publicada es inmutable; crea una nueva versión.")
    if question.version != body.version:
        api_error(409, "VERSION_CONFLICT", "El reactivo cambió. Recarga antes de guardar.")
    if body.enunciado is not None:
        question.enunciado = body.enunciado.strip()
    if body.opciones is not None:
        question.opciones = body.opciones
    if body.clave is not None:
        question.clave_correcta = body.clave
    if question.clave_correcta not in question.opciones:
        api_error(422, "INVALID_KEY", "La clave debe existir entre las opciones.")
    if body.estado not in {"borrador", "aprobado", "rechazado"}:
        api_error(422, "INVALID_REVIEW_STATE", "Estado de revisión inválido.")
    question.estado_revision = body.estado
    question.version += 1
    if body.estado == "aprobado":
        question.revisado_por = user.id
        question.fecha_revision = datetime.now(timezone.utc)
    else:
        question.revisado_por = user.id
        question.fecha_revision = datetime.now(timezone.utc)
    audit(db, user.id, "QUESTION_REVIEW", f"reactivo:{question.id}")
    db.commit()
    return question_json(question, True)


@router.post("/assessments/{id}/publish")
def publish(id: str, body: PublishIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    assessment = db.get(Assessment, id)
    if not assessment:
        api_error(404, "ASSESSMENT_NOT_FOUND", "Evaluación no encontrada.")
    return publish_assessment(db, user, assessment, body.fechaInicio, body.fechaFin, body.version)


@router.post("/assessments/{id}/attempts")
def attempt_action(id: str, body: AttemptIn, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, user, "assessment:solve")
    if user.rol != "estudiante":
        api_error(403, "STUDENT_REQUIRED", "Solo estudiantes pueden resolver evaluaciones.")
    assessment = db.get(Assessment, id)
    if not assessment:
        api_error(404, "ASSESSMENT_NOT_FOUND", "Evaluación no encontrada.")
    can_access_course(db, user, assessment.curso_id)
    if assessment.estado != "publicada":
        api_error(409, "ASSESSMENT_NOT_OPEN", "La evaluación no está publicada.")
    now = datetime.now(timezone.utc)
    start = _aware(assessment.fecha_inicio)
    end = _aware(assessment.fecha_fin)
    if start and now < start:
        api_error(422, "ASSESSMENT_NOT_STARTED", "La evaluación todavía no inició.")
    if end and now > end:
        api_error(422, "ASSESSMENT_EXPIRED", "La fecha de cierre de la evaluación ya venció.")

    attempt = db.query(Attempt).filter(Attempt.evaluacion_id == assessment.id, Attempt.estudiante_id == user.id).first()
    if body.accion == "iniciar":
        if attempt:
            return {"attemptId": attempt.id, "estado": attempt.estado, "puntaje": float(attempt.puntaje) if attempt.puntaje is not None else None}
        attempt = Attempt(evaluacion_id=assessment.id, estudiante_id=user.id)
        db.add(attempt)
        db.flush()
        corr = uid()
        db.add(Event(usuario_seudonimo=user.seudonimo, curso_id=assessment.curso_id, tipo="assessment_start", correlation_id=corr))
        audit(db, user.id, "ATTEMPT_START", f"intento:{attempt.id}", correlation_id=corr)
        db.commit()
        return {"attemptId": attempt.id, "estado": "abierto"}
    if body.accion != "cerrar":
        api_error(422, "INVALID_ACTION", "accion debe ser iniciar o cerrar.")
    if not attempt:
        api_error(409, "ATTEMPT_NOT_STARTED", "Primero inicia el intento.")
    if body.intentoId and body.intentoId != attempt.id:
        api_error(409, "ATTEMPT_MISMATCH", "El intento enviado no corresponde al estudiante y evaluación.")
    if attempt.estado == "cerrado":
        return {"attemptId": attempt.id, "estado": "cerrado", "puntaje": float(attempt.puntaje)}

    questions = db.query(Question).filter(Question.evaluacion_id == assessment.id).all()
    answers = body.respuestas or {}
    known_ids = {q.id for q in questions}
    if any(qid not in known_ids for qid in answers):
        api_error(422, "ANSWER_FOREIGN_QUESTION", "Se recibió una respuesta para un reactivo ajeno a la evaluación.")
    correct = 0
    for question in questions:
        selected = answers.get(question.id)
        ok = selected == question.clave_correcta
        correct += int(ok)
        db.add(Answer(intento_id=attempt.id, reactivo_id=question.id, evaluacion_id=assessment.id, opcion_elegida=selected, es_correcta=ok))
    score = round(20 * correct / len(questions), 2) if questions else 0.0
    attempt.puntaje = score
    attempt.estado = "cerrado"
    attempt.fecha_cierre = now
    corr = uid()
    db.add(Event(usuario_seudonimo=user.seudonimo, curso_id=assessment.curso_id, tipo="assessment_close", correlation_id=corr))
    audit(db, user.id, "ATTEMPT_CLOSE", f"intento:{attempt.id}", correlation_id=corr)
    db.commit()
    return {"attemptId": attempt.id, "estado": "cerrado", "puntaje": score, "correctas": correct, "total": len(questions)}
