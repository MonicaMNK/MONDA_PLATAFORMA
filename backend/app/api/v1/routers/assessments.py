from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from ...deps import current_user
from ....core.errors import api_error
from ....db.audit import audit
from ....db.session import get_db
from ....models import Answer, Assessment, Attempt, Enrollment, Event, Question, User, uid
from ....schemas import AttemptIn, GenerateIn, PublishIn, ReviewIn
from ....schemas.api import ResultsPublishIn
from ....services.access import can_access_course, require_permission, teacher_course
from ....services.assessment_service import generate_assessment, publish_assessment
from ....services.serializers import dtiso, question_json

router = APIRouter(prefix="/api", tags=["Evaluaciones"])


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def results_visible(assessment):
    return bool((assessment.configuracion or {}).get('resultadosPublicados'))


def attempt_json(attempt,assessment):
    return {'attemptId':attempt.id,'estado':attempt.estado,'cierreForzado':attempt.id in (assessment.configuracion or {}).get('intentosCerradosPorDocente',[]),'puntaje':float(attempt.puntaje) if results_visible(assessment) and attempt.puntaje is not None else None,'resultsPublished':results_visible(assessment),'fechaInicio':dtiso(attempt.fecha_inicio),'fechaCierre':dtiso(attempt.fecha_cierre)}


def regrade(db,assessment):
    questions=db.query(Question).filter(Question.evaluacion_id==assessment.id).all()
    keys={q.id:q.clave_correcta for q in questions}
    for attempt in db.query(Attempt).filter(Attempt.evaluacion_id==assessment.id,Attempt.estado=='cerrado').all():
        answers=db.query(Answer).filter(Answer.intento_id==attempt.id).all()
        correct=0
        for answer in answers:
            answer.es_correcta=answer.opcion_elegida==keys.get(answer.reactivo_id)
            correct+=int(answer.es_correcta)
        attempt.puntaje=round(20*correct/len(questions),2) if questions else 0


def assessment_json(db,a,user):
    own=db.query(Attempt).filter(Attempt.evaluacion_id==a.id,Attempt.estudiante_id==user.id).first() if user.rol=='estudiante' else None
    return {'id':a.id,'titulo':a.titulo,'estado':a.estado,'fechaInicio':dtiso(a.fecha_inicio),'fechaFin':dtiso(a.fecha_fin),'version':a.version,'resultsPublished':results_visible(a),'miEstado':'completada' if own and own.estado=='cerrado' else 'en_progreso' if own else 'no_iniciada','miIntento':attempt_json(own,a) if own else None}


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
    return {"items": [assessment_json(db,a,user) for a in rows], "page": page, "total": total}


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
    return {**assessment_json(db,assessment,user), "cursoId": assessment.curso_id, "configuracion": assessment.configuracion, "questions": [question_json(q, include_keys) for q in questions]}


@router.patch("/questions/{questionId}/review")
def review_question(questionId: str, body: ReviewIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    question = db.get(Question, questionId)
    if not question:
        api_error(404, "QUESTION_NOT_FOUND", "Reactivo no encontrado.")
    assessment = db.query(Assessment).filter(Assessment.id==question.evaluacion_id).with_for_update().first()
    teacher_course(db, user, assessment.curso_id)
    if results_visible(assessment):
        api_error(409, "RESULTS_IMMUTABLE", "Los resultados ya están publicados.")
    if assessment.estado != 'borrador' and (body.enunciado is not None or body.opciones is not None):
        api_error(409,'ASSESSMENT_IMMUTABLE','Después de publicar solo puedes corregir la clave y la justificación.')
    if question.version != body.version:
        api_error(409, "VERSION_CONFLICT", "El reactivo cambió. Recarga antes de guardar.")
    if body.enunciado is not None:
        question.enunciado = body.enunciado.strip()
    if body.opciones is not None:
        question.opciones = body.opciones
    if body.clave is not None:
        question.clave_correcta = body.clave
    if body.justificacion is not None:
        question.justificacion=body.justificacion.strip()
        if not question.justificacion:
            api_error(422,'JUSTIFICATION_EMPTY','La justificación no puede estar vacía.')
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
    assessment.version+=1
    if assessment.estado!='borrador':
        regrade(db,assessment)
    db.commit()
    return question_json(question, True)


@router.post("/assessments/{id}/publish")
def publish(id: str, body: PublishIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id==id).with_for_update().first()
    if not assessment:
        api_error(404, "ASSESSMENT_NOT_FOUND", "Evaluación no encontrada.")
    return publish_assessment(db, user, assessment, body.fechaInicio, body.fechaFin, body.version)


@router.post("/assessments/{id}/attempts")
def attempt_action(id: str, body: AttemptIn, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, user, "assessment:solve")
    if user.rol != "estudiante":
        api_error(403, "STUDENT_REQUIRED", "Solo estudiantes pueden resolver evaluaciones.")
    assessment = db.query(Assessment).filter(Assessment.id==id).with_for_update().first()
    if not assessment:
        api_error(404, "ASSESSMENT_NOT_FOUND", "Evaluación no encontrada.")
    can_access_course(db, user, assessment.curso_id)
    attempt = db.query(Attempt).filter(Attempt.evaluacion_id == assessment.id, Attempt.estudiante_id == user.id).with_for_update().first()
    if attempt and attempt.estado=='cerrado':
        return attempt_json(attempt,assessment)
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
            return attempt_json(attempt,assessment)
        attempt = Attempt(evaluacion_id=assessment.id, estudiante_id=user.id)
        db.add(attempt)
        db.flush()
        corr = uid()
        db.add(Event(usuario_seudonimo=user.seudonimo, curso_id=assessment.curso_id, tipo="assessment_start", correlation_id=corr))
        audit(db, user.id, "ATTEMPT_START", f"intento:{attempt.id}", correlation_id=corr)
        db.commit()
        return {"attemptId": attempt.id, "estado": "abierto"}
    if body.accion not in {"cerrar","guardar"}:
        api_error(422, "INVALID_ACTION", "accion debe ser iniciar, guardar o cerrar.")
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
    existing={a.reactivo_id:a for a in db.query(Answer).filter(Answer.intento_id==attempt.id).all()}
    for question in questions:
        selected = answers.get(question.id,existing[question.id].opcion_elegida if question.id in existing else None)
        if selected is not None and selected not in question.opciones:
            api_error(422,'INVALID_OPTION','La opción elegida no pertenece a la pregunta.')
        ok = selected == question.clave_correcta
        correct += int(ok)
        answer=existing.get(question.id)
        if answer:
            answer.opcion_elegida=selected
            answer.es_correcta=ok
        else:
            db.add(Answer(intento_id=attempt.id, reactivo_id=question.id, evaluacion_id=assessment.id, opcion_elegida=selected, es_correcta=ok))
    if body.accion=='guardar':
        db.commit()
        return {**attempt_json(attempt,assessment),'saved':True}
    score = round(20 * correct / len(questions), 2) if questions else 0.0
    attempt.puntaje = score
    attempt.estado = "cerrado"
    attempt.fecha_cierre = now
    corr = uid()
    db.add(Event(usuario_seudonimo=user.seudonimo, curso_id=assessment.curso_id, tipo="assessment_close", correlation_id=corr))
    audit(db, user.id, "ATTEMPT_CLOSE", f"intento:{attempt.id}", correlation_id=corr)
    db.commit()
    return {**attempt_json(attempt,assessment),'message':'Evaluación completada. El docente publicará los resultados.'}


@router.get('/assessments/{id}/submissions')
def submissions(id:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    assessment=db.get(Assessment,id)
    if not assessment:api_error(404,'ASSESSMENT_NOT_FOUND','Evaluación no encontrada.')
    teacher_course(db,user,assessment.curso_id)
    attempts={a.estudiante_id:a for a in db.query(Attempt).filter(Attempt.evaluacion_id==id).all()}
    ids={e.estudiante_id for e in db.query(Enrollment).filter(Enrollment.curso_id==assessment.curso_id,Enrollment.estado=='activa').all()}|set(attempts)
    items=[]
    for sid in ids:
        student=db.get(User,sid);attempt=attempts.get(sid)
        items.append({'estudianteId':sid,'nombre':student.nombre,'correo':student.correo,'estado':'completada' if attempt and attempt.estado=='cerrado' else 'en_progreso' if attempt else 'pendiente','cierreForzado':bool(attempt and attempt.id in (assessment.configuracion or {}).get('intentosCerradosPorDocente',[])),'attemptId':attempt.id if attempt else None,'fechaInicio':dtiso(attempt.fecha_inicio) if attempt else None,'fechaCierre':dtiso(attempt.fecha_cierre) if attempt else None,'duracionSegundos':int((_aware(attempt.fecha_cierre)-_aware(attempt.fecha_inicio)).total_seconds()) if attempt and attempt.fecha_cierre else None,'puntaje':float(attempt.puntaje) if attempt and attempt.puntaje is not None else None})
    return {'items':sorted(items,key=lambda x:x['nombre']), 'total':len(items),'completed':sum(x['estado']=='completada' for x in items),'inProgress':sum(x['estado']=='en_progreso' for x in items),'resultsPublished':results_visible(assessment)}


@router.post('/assessments/{id}/results/publish')
def publish_results(id:str,body:ResultsPublishIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    assessment=db.query(Assessment).filter(Assessment.id==id).with_for_update().first()
    if not assessment:api_error(404,'ASSESSMENT_NOT_FOUND','Evaluación no encontrada.')
    teacher_course(db,user,assessment.curso_id)
    if results_visible(assessment):return {'published':True,'version':assessment.version}
    if body.version!=assessment.version:api_error(409,'VERSION_CONFLICT','La evaluación cambió; recarga antes de publicar.')
    if assessment.estado=='borrador':api_error(409,'ASSESSMENT_NOT_PUBLISHED','Primero publica la evaluación.')
    questions=db.query(Question).filter(Question.evaluacion_id==id).all()
    if not questions or any(q.estado_revision!='aprobado' for q in questions):api_error(409,'REVIEW_REQUIRED','Revisa y aprueba todas las claves y justificaciones.')
    forced=[]
    for attempt in db.query(Attempt).filter(Attempt.evaluacion_id==id,Attempt.estado=='abierto').all():
        forced.append(attempt.id)
        attempt.estado='cerrado';attempt.fecha_cierre=datetime.now(timezone.utc)
    db.flush()
    regrade(db,assessment)
    assessment.estado='cerrada'
    assessment.configuracion={**assessment.configuracion,'resultadosPublicados':True,'intentosCerradosPorDocente':forced,'fechaPublicacionResultados':datetime.now(timezone.utc).isoformat()}
    assessment.version+=1
    audit(db,user.id,'RESULTS_PUBLISH',f'evaluacion:{id}')
    db.commit()
    return {'published':True,'version':assessment.version,'estado':assessment.estado}


@router.get('/assessments/{id}/results')
def my_results(id:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    assessment=db.get(Assessment,id)
    if not assessment:api_error(404,'ASSESSMENT_NOT_FOUND','Evaluación no encontrada.')
    can_access_course(db,user,assessment.curso_id)
    if not results_visible(assessment):api_error(409,'RESULTS_PENDING','El docente aún no publica los resultados.')
    attempt=db.query(Attempt).filter(Attempt.evaluacion_id==id,Attempt.estudiante_id==user.id,Attempt.estado=='cerrado').first()
    if not attempt:api_error(404,'ATTEMPT_NOT_FOUND','No tienes una entrega completada.')
    answers={a.reactivo_id:a for a in db.query(Answer).filter(Answer.intento_id==attempt.id).all()}
    questions=db.query(Question).filter(Question.evaluacion_id==id).order_by(Question.id).all()
    return {**attempt_json(attempt,assessment),'assessmentId':id,'titulo':assessment.titulo,'questions':[{**question_json(q,True),'miRespuesta':answers[q.id].opcion_elegida if q.id in answers else None,'correcta':answers[q.id].es_correcta if q.id in answers else False} for q in questions]}


@router.get('/assessments/{id}/my-attempt')
def own_attempt(id:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    assessment=db.get(Assessment,id)
    if not assessment:api_error(404,'ASSESSMENT_NOT_FOUND','Evaluación no encontrada.')
    can_access_course(db,user,assessment.curso_id)
    attempt=db.query(Attempt).filter(Attempt.evaluacion_id==id,Attempt.estudiante_id==user.id).first()
    if not attempt:return {'estado':'no_iniciada','respuestas':{}}
    return {**attempt_json(attempt,assessment),'respuestas':{a.reactivo_id:a.opcion_elegida for a in db.query(Answer).filter(Answer.intento_id==attempt.id).all()}}
