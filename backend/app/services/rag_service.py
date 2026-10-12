from __future__ import annotations

import time

from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.errors import api_error
from ..db.audit import audit
from ..models import Config, Conversation, Event, Message, User, uid
from ..rag import get_provider_with_fallback
from ..repositories import VectorStoreRepository
from .access import can_access_course, require_permission
from .tracing import trace_rag


def _config(db: Session) -> dict:
    row = db.get(Config, "rag")
    return row.valor if row else {"topK": settings.rag_top_k, "umbral": settings.rag_similarity_threshold, "mode": settings.rag_mode}


def query_rag(db: Session, user: User, course_id: str, question: str, conversation_id: str | None = None) -> dict:
    require_permission(db, user, "rag:query")
    can_access_course(db, user, course_id)
    conv = None
    if conversation_id:
        conv = db.get(Conversation, conversation_id)
        if not conv or conv.usuario_id != user.id or conv.curso_id != course_id:
            api_error(403, "CONVERSATION_FORBIDDEN", "Conversación no autorizada.")
    if conv is None:
        conv = Conversation(usuario_id=user.id, curso_id=course_id, estado="activa")
        db.add(conv)
        db.flush()

    cfg = _config(db)
    mode = str(cfg.get("mode") or settings.rag_mode)
    top_k = int(cfg.get("topK", settings.rag_top_k))
    threshold = float(cfg.get("umbral", settings.rag_similarity_threshold))
    corr = uid()
    db.add(Message(conversacion_id=conv.id, autor="usuario", contenido=question, fuentes=[], score_max=None, evidencia_suficiente=False, correlation_id=corr))

    started = time.perf_counter()
    vector_store = VectorStoreRepository(db)
    provider, warning = get_provider_with_fallback(mode, llm_model=cfg.get("modelo"), ollama_model=cfg.get("ollamaModel"))
    provider_latency = 0.0
    input_tokens = output_tokens = None
    try:
        if provider.supports_embeddings:
            t = time.perf_counter()
            vectors = provider.embed([question], task="query")
            provider_latency += time.perf_counter() - t
            if not vectors or len(vectors[0]) != 768:
                raise ValueError("Embedding de consulta inválido; se esperaban 768 dimensiones")
            ranked = vector_store.search(course_id=course_id, question=question, top_k=max(top_k, 1), query_vector=vectors[0])
        else:
            ranked = vector_store.search(course_id=course_id, question=question, top_k=top_k)
    except Exception as exc:
        if not settings.rag_allow_fallback:
            raise
        ranked = vector_store.search(course_id=course_id, question=question, top_k=top_k)
        warning = str(exc)
        from ..rag.providers.fallback import FallbackProvider
        provider = FallbackProvider()

    sources = [{"fragmentId": f.id, "contentId": f.contenido_id, "ordinal": f.ordinal, "location": f.ubicacion, "score": round(float(f.score), 4), "excerpt": f.texto[:360]} for f in ranked]
    max_score = max((f.score for f in ranked), default=0.0)
    # En fallback la similitud es léxica normalizada y usa el mismo umbral configurable como criterio operativo.
    sufficient = bool(ranked and max_score >= threshold)
    if not sufficient:
        answer = "No encuentro evidencia suficiente en los materiales autorizados de este curso para responder con confianza."
    elif provider.supports_generation:
        context = "\n\n".join(f"[F{i + 1} | fragmentId={f.id}] {f.texto}" for i, f in enumerate(ranked))
        prompt = (
            "Eres el Tutor Monda. Responde en español únicamente con la evidencia del contexto. "
            "No uses conocimiento externo. Cita las fuentes como [F1], [F2], etc. Si el contexto no alcanza, responde evidencia insuficiente.\n\n"
            f"CONTEXTO:\n{context}\n\nPREGUNTA:\n{question}"
        )
        t = time.perf_counter()
        try:
            generated = provider.generate(prompt)
            provider_latency += time.perf_counter() - t
            answer = generated.text.strip()
            input_tokens = generated.input_tokens
            output_tokens = generated.output_tokens
            if not answer:
                raise ValueError("Generación vacía")
        except Exception as exc:
            if not settings.rag_allow_fallback:
                raise
            warning = (warning + "; " if warning else "") + str(exc)
            answer = "Según los materiales del curso: " + " ".join(f.texto for f in ranked[:2])
    else:
        answer = "Según los materiales del curso: " + " ".join(f.texto for f in ranked[:2])

    msg = Message(conversacion_id=conv.id, autor="tutor", contenido=answer, fuentes=sources, score_max=float(max_score) if ranked else None, evidencia_suficiente=sufficient, correlation_id=corr)
    db.add(msg)
    db.add(Event(usuario_seudonimo=user.seudonimo, curso_id=course_id, tipo="rag_query", correlation_id=corr))
    audit(db, user.id, "RAG_QUERY", f"curso:{course_id}", correlation_id=corr)
    db.commit()

    elapsed = time.perf_counter() - started
    trace_rag({
        "correlationId": corr,
        "courseId": course_id,
        "provider": provider.name,
        "model": provider.llm_model,
        "embeddingModel": provider.embedding_model,
        "evidenceSufficient": sufficient,
        "maxScore": max_score,
        "sourceCount": len(sources),
        "latencyMs": round(elapsed * 1000, 2),
        "providerLatencyMs": round(provider_latency * 1000, 2),
        "inputTokens": input_tokens,
        "outputTokens": output_tokens,
        "question": question,
        "answer": answer,
    })
    return {"answer": answer, "sources": sources, "evidenceSufficient": sufficient, "correlationId": corr, "conversationId": conv.id, "messageId": msg.id, "mode": provider.name, "providerWarning": warning}
