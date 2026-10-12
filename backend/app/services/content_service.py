from __future__ import annotations

import hashlib
import time
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.errors import api_error
from ..db.audit import audit
from ..models import Config, Content, Job, RAGFragment, User, uid
from ..rag import chunk_text, extract_text, get_provider_with_fallback
from .access import teacher_course
from .storage import get_storage


def create_content(db: Session, user: User, course_id: str, filename: str, media_type: str | None, data: bytes, documento_id: str | None, version: int) -> Content:
    teacher_course(db, user, course_id)
    ext = Path(filename).suffix.lower()
    if ext not in {".pdf", ".docx"}:
        api_error(415, "UNSUPPORTED_MEDIA", "Solo se admiten PDF o DOCX.")
    if not data:
        api_error(422, "EMPTY_FILE", "El archivo está vacío.")
    if len(data) > settings.max_upload_bytes:
        api_error(413, "FILE_TOO_LARGE", "El archivo supera 20 MiB.")
    if version < 1:
        api_error(422, "INVALID_VERSION", "La versión debe ser mayor o igual a 1.")
    if documento_id:
        try:
            doc_id = str(uuid.UUID(documento_id))
        except Exception:
            api_error(422, "DOCUMENT_ID_INVALID", "documentoId debe ser UUID válido.")
    else:
        doc_id = uid()
    if db.query(Content).filter(Content.documento_id == doc_id, Content.version == version).first():
        api_error(409, "CONTENT_VERSION_EXISTS", "Ya existe esta versión del documento.")
    cid = uid()
    storage_key = f"courses/{course_id}/{doc_id}/v{version}/{cid}{ext}"
    stored = get_storage().put(storage_key, data, media_type)
    canonical_mime = "application/pdf" if ext == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    content = Content(
        id=cid,
        documento_id=doc_id,
        curso_id=course_id,
        version=version,
        nombre_original=filename,
        mime_type=canonical_mime,
        tamano_bytes=len(data),
        s3_key=stored,
        hash_sha256=hashlib.sha256(data).hexdigest(),
        autor_id=user.id,
        estado_indexacion="pendiente",
        activo=False,
        modelo_embedding="pendiente",
    )
    db.add(content)
    audit(db, user.id, "CONTENT_UPLOAD", f"contenido:{cid}")
    db.commit()
    return content


def index_content(db: Session, user: User, content: Content, mode: str | None = None) -> Job:
    teacher_course(db, user, content.curso_id)
    if content.estado_indexacion == "indexado" and content.activo:
        prior = Job(usuario_id=user.id, curso_id=content.curso_id, tipo="ingesta", estado="completado", resultado={"contentId": content.id, "fragmentCount": db.query(RAGFragment).filter(RAGFragment.contenido_id == content.id).count(), "idempotent": True}, correlation_id=uid())
        db.add(prior)
        db.commit()
        return prior

    job = Job(usuario_id=user.id, curso_id=content.curso_id, tipo="ingesta", estado="procesando", resultado={"contentId": content.id}, correlation_id=uid())
    db.add(job)
    content.estado_indexacion = "procesando"
    db.commit()

    try:
        storage = get_storage()
        path = storage.local_path(content.s3_key)
        text, locations = extract_text(path)
        chunks = chunk_text(text, 512, 50)
        if not chunks:
            raise ValueError("No se encontró texto extraíble")

        rag_cfg = db.get(Config, "rag")
        cfg = rag_cfg.valor if rag_cfg else {}
        selected_mode = mode or cfg.get("mode") or settings.rag_mode
        provider, provider_warning = get_provider_with_fallback(selected_mode, ollama_model=cfg.get("ollamaModel"), llm_model=cfg.get("modelo"))
        vectors: list[list[float] | None]
        if provider.supports_embeddings:
            try:
                generated = provider.embed(chunks, task="document")
                if len(generated) != len(chunks) or any(len(v) != 768 for v in generated):
                    raise ValueError(f"El proveedor {provider.name} debe producir vectores de 768 dimensiones")
                vectors = generated
            except Exception as provider_exc:
                if not settings.rag_allow_fallback:
                    raise
                from ..rag.providers.fallback import FallbackProvider
                provider_warning = (provider_warning + "; " if provider_warning else "") + f"{type(provider_exc).__name__}: proveedor de embeddings no disponible"
                provider = FallbackProvider()
                vectors = [None] * len(chunks)
        else:
            vectors = [None] * len(chunks)

        # Solo reemplazamos fragmentos cuando toda la extracción/vectorización fue válida.
        db.query(RAGFragment).filter(RAGFragment.contenido_id == content.id).delete(synchronize_session=False)
        for ordinal, (piece, vector) in enumerate(zip(chunks, vectors), 1):
            fragment_id = str(uuid.uuid5(uuid.UUID(content.id), f"{ordinal}:{provider.embedding_model}"))
            fragment_hash = hashlib.sha256(
                f"{content.documento_id}:{content.version}:{ordinal}:{provider.embedding_model}:{piece}".encode("utf-8")
            ).hexdigest()
            db.add(RAGFragment(
                id=fragment_id,
                contenido_id=content.id,
                curso_id=content.curso_id,
                ordinal=ordinal,
                texto=piece,
                ubicacion=f"fragmento {ordinal}",
                metadata_json={"filename": content.nombre_original, "version": content.version},
                embedding=vector,
                embedding_model=provider.embedding_model,
                embedding_provider=provider.name,
                hash_fragmento=fragment_hash,
            ))
        db.query(Content).filter(Content.documento_id == content.documento_id).update({"activo": False}, synchronize_session=False)
        content.activo = True
        content.estado_indexacion = "indexado"
        content.modelo_embedding = provider.embedding_model
        job.estado = "completado"
        job.resultado = {"contentId": content.id, "fragmentCount": len(chunks), "provider": provider.name, "providerWarning": provider_warning}
        audit(db, user.id, "CONTENT_INDEX", f"contenido:{content.id}", correlation_id=job.correlation_id)
        db.commit()
    except Exception as exc:
        db.rollback()
        content = db.get(Content, content.id)
        job = db.get(Job, job.id)
        content.estado_indexacion = "error"
        content.activo = False
        job.estado = "error"
        job.resultado = {"contentId": content.id, "errorCode": "INDEX_ERROR", "message": str(exc)[:500]}
        audit(db, user.id, "CONTENT_INDEX", f"contenido:{content.id}", result="error", correlation_id=job.correlation_id)
        db.commit()
    return job
