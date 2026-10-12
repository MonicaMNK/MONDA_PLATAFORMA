from __future__ import annotations

import json
import re
from datetime import timezone

from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.errors import api_error
from ..db.audit import audit
from ..models import Answer, Assessment, Config, Content, Event, Job, Question, RAGFragment, User, uid
from ..rag import get_provider_with_fallback, lexical_search
from .access import can_access_course, require_permission, teacher_course

BLOOM = {"recordar", "comprender", "aplicar", "analizar", "evaluar", "crear"}
DIFFICULTIES = {"baja", "media", "alta"}


def _extract_json(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I | re.S)
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        obj = json.loads(text[start : end + 1])
        return obj.get("questions") or obj.get("reactivos") or []
    raise ValueError("No se encontró JSON de reactivos")


def _fallback_questions(fragments, tema: str, bloom: str, dificultad: str, cantidad: int) -> list[dict]:
    rows = []
    for i in range(cantidad):
        frag = fragments[i % len(fragments)]
        statement = frag.texto.strip()
        if len(statement) > 220:
            statement = statement[:217].rstrip() + "..."
        rows.append({
            "enunciado": f"Según el material del curso, ¿qué afirmación está respaldada respecto de {tema}?",
            "opciones": {"A": statement, "B": "Una afirmación no indicada en el material", "C": "Una conclusión contraria a la evidencia", "D": "Ninguna de las anteriores"},
            "clave": "A",
            "justificacion": f"La opción A se fundamenta en el fragmento {frag.ordinal} del material activo.",
            "nivelBloom": bloom,
            "dificultad": dificultad,
            "fragmentId": frag.id,
            "contentId": frag.contenido_id,
        })
    return rows


def generate_assessment(db: Session, user: User, course_id: str, tema: str, bloom: str, dificultad: str, cantidad: int, tipo: str) -> dict:
    require_permission(db, user, "assessment:write")
    teacher_course(db, user, course_id)
    if bloom not in BLOOM or dificultad not in DIFFICULTIES or tipo != "opcion_multiple":
        api_error(422, "ASSESSMENT_CONFIG_INVALID", "Bloom, dificultad o tipo de reactivo inválido.")
    fragments = lexical_search(db, course_id, tema, max(cantidad, 4))
    if not fragments:
        fragments = [
            type("F", (), {"id": f.id, "contenido_id": f.contenido_id, "ordinal": f.ordinal, "texto": f.texto})
            for f in db.query(RAGFragment).join(Content, Content.id == RAGFragment.contenido_id).filter(RAGFragment.curso_id == course_id, Content.activo.is_(True), Content.estado_indexacion == "indexado").limit(max(cantidad, 4)).all()
        ]
    if not fragments:
        api_error(422, "NO_CONTENT", "No hay material indexado para generar reactivos.")

    job = Job(usuario_id=user.id, curso_id=course_id, tipo="generacion", estado="procesando", resultado={}, correlation_id=uid())
    db.add(job)
    db.flush()
    cfg_row = db.get(Config, "rag")
    cfg = cfg_row.valor if cfg_row else {}
    provider, warning = get_provider_with_fallback(cfg.get("mode"), llm_model=cfg.get("modelo"), ollama_model=cfg.get("ollamaModel"))
    questions = None
    if provider.supports_generation:
        context = "\n\n".join(f"fragmentId={f.id}; contentId={f.contenido_id}; texto={f.texto}" for f in fragments[:8])
        prompt = f"""Genera exactamente {cantidad} reactivos objetivos en español sobre: {tema}.
Nivel Bloom: {bloom}. Dificultad: {dificultad}. Solo usa el contexto y no inventes fuentes.
Devuelve EXCLUSIVAMENTE un arreglo JSON. Cada objeto debe contener:
enunciado, opciones (objeto A/B/C/D), clave, justificacion, nivelBloom, dificultad, fragmentId, contentId.
La clave debe ser una de A/B/C/D y fragmentId/contentId deben existir en el contexto.
CONTEXTO:\n{context}"""
        try:
            generated = provider.generate(prompt)
            parsed = _extract_json(generated.text)
            if isinstance(parsed, list) and len(parsed) >= cantidad:
                questions = parsed[:cantidad]
        except Exception as exc:
            warning = (warning + "; " if warning else "") + str(exc)
    if not questions:
        questions = _fallback_questions(fragments, tema, bloom, dificultad, cantidad)

    allowed_frag = {f.id: f for f in fragments}
    assessment = Assessment(curso_id=course_id, titulo=f"Evaluación: {tema}", configuracion={"tema": tema, "bloom": bloom, "dificultad": dificultad, "cantidad": cantidad, "tipo": tipo, "generationMode": provider.name}, estado="borrador")
    db.add(assessment)
    db.flush()
    created = 0
    for item in questions:
        fragment_id = str(item.get("fragmentId") or "")
        frag = allowed_frag.get(fragment_id)
        if not frag:
            frag = fragments[created % len(fragments)]
        options = item.get("opciones") if isinstance(item.get("opciones"), dict) else None
        key = str(item.get("clave") or "")
        if not options or key not in options:
            continue
        q = Question(
            evaluacion_id=assessment.id,
            enunciado=str(item.get("enunciado") or "").strip(),
            opciones={str(k): str(v) for k, v in options.items()},
            clave_correcta=key,
            justificacion=str(item.get("justificacion") or "Requiere revisión docente."),
            nivel_bloom=str(item.get("nivelBloom") or bloom) if str(item.get("nivelBloom") or bloom) in BLOOM else bloom,
            dificultad=str(item.get("dificultad") or dificultad) if str(item.get("dificultad") or dificultad) in DIFFICULTIES else dificultad,
            contenido_id=frag.contenido_id,
            fragmento_id=frag.id,
            estado_revision="borrador",
        )
        if not q.enunciado:
            continue
        db.add(q)
        created += 1
    if created == 0:
        db.rollback()
        api_error(503, "ASSESSMENT_GENERATION_FAILED", "No fue posible producir reactivos válidos.")
    job.estado = "completado"
    job.resultado = {"assessmentId": assessment.id, "questionCount": created, "provider": provider.name, "providerWarning": warning}
    audit(db, user.id, "ASSESSMENT_GENERATE", f"evaluacion:{assessment.id}", correlation_id=job.correlation_id)
    db.commit()
    return {"jobId": job.id, "estado": job.estado, "assessmentId": assessment.id, "questionCount": created, "mode": provider.name, "providerWarning": warning}


def publish_assessment(db: Session, user: User, assessment: Assessment, start, end, version: int) -> dict:
    teacher_course(db, user, assessment.curso_id)
    if assessment.estado!='borrador':
        api_error(409,'ASSESSMENT_ALREADY_PUBLISHED','La evaluación ya se publicó; no puede reabrirse.')
    if assessment.version != version:
        api_error(409, "VERSION_CONFLICT", "La evaluación cambió. Recarga antes de publicar.")
    if end <= start:
        api_error(422, "INVALID_DATES", "La fecha fin debe ser posterior al inicio.")
    questions = db.query(Question).filter(Question.evaluacion_id == assessment.id).all()
    if not questions or any(q.estado_revision != "aprobado" for q in questions):
        api_error(409, "REVIEW_REQUIRED", "Todos los reactivos deben estar aprobados por un docente antes de publicar.")
    assessment.estado = "publicada"
    assessment.fecha_inicio = start
    assessment.fecha_fin = end
    assessment.version += 1
    audit(db, user.id, "ASSESSMENT_PUBLISH", f"evaluacion:{assessment.id}")
    db.commit()
    return {"id": assessment.id, "estado": assessment.estado, "version": assessment.version}
