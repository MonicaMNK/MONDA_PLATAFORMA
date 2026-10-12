from __future__ import annotations

import math
import re
from dataclasses import dataclass

from sqlalchemy import text, bindparam
from sqlalchemy.orm import Session

from ..models import Content, RAGFragment


@dataclass
class RetrievedFragment:
    id: str
    contenido_id: str
    ordinal: int
    texto: str
    ubicacion: str | None
    score: float
    metadata: dict


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return -1.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else -1.0


def vector_search(db: Session, course_id: str, query_vector: list[float], top_k: int, embedding_model: str, embedding_provider: str, content_ids: list[str] | None = None) -> list[RetrievedFragment]:
    if content_ids == []:
        return []
    if db.bind and db.bind.dialect.name == "postgresql":
        literal = "[" + ",".join(f"{x:.10g}" for x in query_vector) + "]"
        sql = text("""
            SELECT f.id::text, f.contenido_id::text, f.ordinal, f.texto, f.ubicacion,
                   f.metadata, 1 - (f.embedding <=> CAST(:q AS vector)) AS score
            FROM fragmentos_rag f
            JOIN contenidos c ON c.id = f.contenido_id
            WHERE f.curso_id = CAST(:course_id AS uuid)
              AND c.activo = true AND c.estado_indexacion = 'indexado'
              AND f.embedding IS NOT NULL
              AND f.embedding_model = :model AND f.embedding_provider = :provider
            ORDER BY f.embedding <=> CAST(:q AS vector)
            LIMIT :limit
        """)
        params={"q": literal, "course_id": course_id, "limit": max(1, top_k), "model": embedding_model, "provider": embedding_provider}
        if content_ids is not None:
            sql=text(sql.text.replace('ORDER BY', 'AND f.contenido_id::text IN :content_ids ORDER BY')).bindparams(bindparam('content_ids',expanding=True))
            params['content_ids']=content_ids
        rows = db.execute(sql, params).mappings().all()
        return [RetrievedFragment(id=r["id"], contenido_id=r["contenido_id"], ordinal=r["ordinal"], texto=r["texto"], ubicacion=r["ubicacion"], score=float(r["score"]), metadata=r["metadata"] or {}) for r in rows]

    query = db.query(RAGFragment).join(Content, Content.id == RAGFragment.contenido_id).filter(
        RAGFragment.curso_id == course_id, Content.activo.is_(True), Content.estado_indexacion == "indexado",
        RAGFragment.embedding_model == embedding_model, RAGFragment.embedding_provider == embedding_provider
    )
    if content_ids is not None:
        query=query.filter(RAGFragment.contenido_id.in_(content_ids))
    rows=query.all()
    ranked = []
    for row in rows:
        if row.embedding:
            ranked.append(RetrievedFragment(row.id, row.contenido_id, row.ordinal, row.texto, row.ubicacion, _cosine(query_vector, list(row.embedding)), row.metadata_json or {}))
    return sorted(ranked, key=lambda x: x.score, reverse=True)[:top_k]


def lexical_search(db: Session, course_id: str, question: str, top_k: int, content_ids: list[str] | None = None) -> list[RetrievedFragment]:
    if content_ids == []:
        return []
    query = db.query(RAGFragment).join(Content, Content.id == RAGFragment.contenido_id).filter(
        RAGFragment.curso_id == course_id, Content.activo.is_(True), Content.estado_indexacion == "indexado"
    )
    if content_ids is not None:
        query=query.filter(RAGFragment.contenido_id.in_(content_ids))
    rows=query.all()
    query_terms = {t for t in re.findall(r"[\wáéíóúñü]+", question.lower()) if len(t) > 2}
    ranked: list[RetrievedFragment] = []
    for row in rows:
        words = re.findall(r"[\wáéíóúñü]+", row.texto.lower())
        if not words:
            continue
        unique = set(words)
        overlap = len(query_terms & unique)
        coverage = overlap / max(1, len(query_terms))
        density = overlap / max(1, math.sqrt(len(unique)))
        score = min(1.0, 0.78 * coverage + 0.22 * density)
        if overlap:
            ranked.append(RetrievedFragment(row.id, row.contenido_id, row.ordinal, row.texto, row.ubicacion, score, row.metadata_json or {}))
    return sorted(ranked, key=lambda x: x.score, reverse=True)[:top_k]
