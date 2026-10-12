from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..db.audit import audit
from ..models import Alert, Assessment, Attempt, Config, Conversation, Enrollment, Event, Message, Rating, User
from .access import teacher_course


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def ensure_alerts(db: Session, course_id: str) -> list[Alert]:
    config=db.get(Config,'alerts')
    cfg=config.valor if config else {}
    threshold=float(cfg.get('promedioMinimo',11));days=int(cfg.get('inactividadDias',7))
    now=utcnow()
    enrollments=db.query(Enrollment).filter(Enrollment.curso_id==course_id,Enrollment.estado=='activa').all()
    active={e.estudiante_id for e in enrollments}
    for enrollment in enrollments:
        student=db.get(User,enrollment.estudiante_id)
        attempts=db.query(Attempt).join(Assessment,Attempt.evaluacion_id==Assessment.id).filter(Assessment.curso_id==course_id,Attempt.estudiante_id==student.id,Attempt.estado=='cerrado').all()
        scores=[float(a.puntaje) for a in attempts if a.puntaje is not None]
        avg=sum(scores)/len(scores) if scores else None
        latest=db.query(Event).filter(Event.usuario_seudonimo==student.seudonimo,Event.curso_id==course_id).order_by(Event.creado_en.desc()).first()
        last=_aware(latest.creado_en) if latest else _aware(enrollment.creado_en)
        elapsed=max(0,(now-last).days) if last else 0
        conditions={'promedio_bajo':(avg is not None and avg<threshold,{'promedio':round(avg,2) if avg is not None else None,'umbral':threshold,'intentos':len(scores),'fechaCorte':now.isoformat()}),'inactividad_7d':(elapsed>=days,{'dias':elapsed,'umbralDias':days,'ultimaActividad':last.isoformat() if last else None,'fechaCorte':now.isoformat()})}
        for rule,(trigger,evidence) in conditions.items():
            old=db.query(Alert).filter(Alert.estudiante_id==student.id,Alert.curso_id==course_id,Alert.regla==rule).order_by(Alert.creado_en.desc()).first()
            if trigger:
                if old:
                    was_resolved=bool((old.evidencia or {}).get('resuelta'))
                    old.evidencia={**(old.evidencia or {}),**evidence,'resuelta':False}
                    if was_resolved:old.estado='abierta';old.revisado_por=None;old.fecha_revision=None
                else:db.add(Alert(estudiante_id=student.id,curso_id=course_id,regla=rule,evidencia={**evidence,'resuelta':False}))
            elif old:
                old.evidencia={**(old.evidencia or {}),**evidence,'resuelta':True}
    for alert in db.query(Alert).filter(Alert.curso_id==course_id).all():
        if alert.estudiante_id not in active:alert.evidencia={**(alert.evidencia or {}),'resuelta':True}
    db.commit()
    return db.query(Alert).filter(Alert.curso_id==course_id).order_by(Alert.creado_en.desc()).all()


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
        "alertas": [{"id": a.id, "estudianteId": a.estudiante_id, "estudiante": db.get(User,a.estudiante_id).nombre, "regla": a.regla, "evidencia": a.evidencia, "estado": a.estado} for a in alerts],
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
    writer.writerow(["seudonimo", "evaluacion", "puntaje", "fecha_cierre", "fecha_corte", "fecha_inicio", "duracion_segundos"])
    cut = corte or utcnow()
    for attempt, student, assessment in q.all():
        duration=int((_aware(attempt.fecha_cierre)-_aware(attempt.fecha_inicio)).total_seconds())
        writer.writerow([safe_csv(student.seudonimo), safe_csv(assessment.titulo), float(attempt.puntaje), _aware(attempt.fecha_cierre).isoformat(), cut.isoformat(),_aware(attempt.fecha_inicio).isoformat(),duration])
    audit(db, user.id, "REPORT_EXPORT", f"curso:{course_id}")
    db.commit()
    return out.getvalue().encode("utf-8-sig")
