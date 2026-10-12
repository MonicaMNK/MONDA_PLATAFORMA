from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..db.audit import audit
from ..models import Alert, Assessment, Attempt, Conversation, Enrollment, Event, Message, Rating, User
from .access import teacher_course


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def ensure_alerts(db: Session, course_id: str) -> list[Alert]:
    enrollments = db.query(Enrollment).filter(Enrollment.curso_id == course_id, Enrollment.estado == "activa").all()
    for enrollment in enrollments:
        attempts = (
            db.query(Attempt)
            .join(Assessment, Attempt.evaluacion_id == Assessment.id)
            .filter(Assessment.curso_id == course_id, Attempt.estudiante_id == enrollment.estudiante_id, Attempt.estado == "cerrado")
            .all()
        )
        scores = [float(x.puntaje) for x in attempts if x.puntaje is not None]
        if scores:
            avg = sum(scores) / len(scores)
            if avg < 11:
                exists = db.query(Alert).filter(Alert.estudiante_id == enrollment.estudiante_id, Alert.curso_id == course_id, Alert.regla == "promedio_bajo", Alert.estado == "abierta").first()
                if not exists:
                    db.add(Alert(estudiante_id=enrollment.estudiante_id, curso_id=course_id, regla="promedio_bajo", evidencia={"promedio": round(avg, 2), "umbral": 11, "intentos": len(scores), "fechaCorte": utcnow().isoformat()}))
        latest = db.query(Event).filter(Event.usuario_seudonimo == db.get(User, enrollment.estudiante_id).seudonimo, Event.curso_id == course_id).order_by(Event.creado_en.desc()).first()
        if latest and (_aware(latest.creado_en) or utcnow()) <= utcnow() - timedelta(days=7):
            exists = db.query(Alert).filter(Alert.estudiante_id == enrollment.estudiante_id, Alert.curso_id == course_id, Alert.regla == "inactividad_7d", Alert.estado == "abierta").first()
            if not exists:
                db.add(Alert(estudiante_id=enrollment.estudiante_id, curso_id=course_id, regla="inactividad_7d", evidencia={"dias": 7, "ultimaActividad": latest.creado_en.isoformat()}))
    db.commit()
    return db.query(Alert).filter(Alert.curso_id == course_id).all()


def analytics(db: Session, user: User, course_id: str, desde: datetime | None = None, hasta: datetime | None = None, corte: datetime | None = None) -> dict:
    teacher_course(db, user, course_id)
    enrollments = db.query(Enrollment).filter(Enrollment.curso_id == course_id, Enrollment.estado == "activa").all()
    q = db.query(Attempt).join(Assessment, Attempt.evaluacion_id == Assessment.id).filter(Assessment.curso_id == course_id, Attempt.estado == "cerrado")
    if desde:
        q = q.filter(Attempt.fecha_cierre >= desde)
    if hasta:
        q = q.filter(Attempt.fecha_cierre <= hasta)
    attempts = q.all()
    scores = [float(x.puntaje) for x in attempts if x.puntaje is not None]
    avg = round(sum(scores) / len(scores), 2) if scores else None
    published = db.query(Assessment).filter(Assessment.curso_id == course_id, Assessment.estado.in_(["publicada", "cerrada"])).count()
    ratings = db.query(Rating).join(Message, Rating.mensaje_id == Message.id).join(Conversation, Message.conversacion_id == Conversation.id).filter(Conversation.curso_id == course_id).all()
    utility = round(100 * sum(1 for x in ratings if x.util) / len(ratings), 2) if ratings else None
    alerts = ensure_alerts(db, course_id)
    return {
        "indicadores": {"estudiantesActivos": len(enrollments), "promedio": avg, "intentosCerrados": len(attempts), "evaluacionesPublicadas": published, "utilidadTutorPct": utility},
        "alertas": [{"id": a.id, "estudianteId": a.estudiante_id, "regla": a.regla, "evidencia": a.evidencia, "estado": a.estado} for a in alerts],
        "fechaCorte": (corte or utcnow()).isoformat(),
    }


def safe_csv(value) -> str:
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        text = "'" + text
    return text


def export_csv(db: Session, user: User, course_id: str, desde: datetime | None = None, hasta: datetime | None = None, corte: datetime | None = None) -> bytes:
    teacher_course(db, user, course_id)
    q = db.query(Attempt, User, Assessment).join(User, Attempt.estudiante_id == User.id).join(Assessment, Attempt.evaluacion_id == Assessment.id).filter(Assessment.curso_id == course_id, Attempt.estado == "cerrado")
    if desde:
        q = q.filter(Attempt.fecha_cierre >= desde)
    if hasta:
        q = q.filter(Attempt.fecha_cierre <= hasta)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["seudonimo", "evaluacion", "puntaje", "fecha_cierre", "fecha_corte"])
    cut = corte or utcnow()
    for attempt, student, assessment in q.all():
        writer.writerow([safe_csv(student.seudonimo), safe_csv(assessment.titulo), float(attempt.puntaje), attempt.fecha_cierre.isoformat(), cut.isoformat()])
    audit(db, user.id, "REPORT_EXPORT", f"curso:{course_id}")
    db.commit()
    return out.getvalue().encode("utf-8-sig")
