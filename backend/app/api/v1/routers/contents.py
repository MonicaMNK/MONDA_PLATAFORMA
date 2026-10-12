from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, Header, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ...deps import current_user
from ....core.errors import api_error
from ....db.session import get_db
from ....models import Content, Job, RAGFragment, User
from ....services.access import can_access_course
from ....services.content_service import create_content, index_content
from ....services.serializers import content_json
from ....services.storage import get_storage

router = APIRouter(prefix="/api", tags=["Contenidos"])


@router.post("/courses/{courseId}/contents", status_code=201)
async def upload_content(courseId: str, file: UploadFile = File(...), documentoId: str | None = Form(None), version: int = Form(1), user: User = Depends(current_user), db: Session = Depends(get_db)):
    data = await file.read()
    content = create_content(db, user, courseId, file.filename or "material", file.content_type, data, documentoId, version)
    return {"contentId": content.id, "documentoId": content.documento_id, "version": content.version, "estado": content.estado_indexacion}


@router.post("/contents/{contentId}/index", status_code=202)
def request_index(contentId: str, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), user: User = Depends(current_user), db: Session = Depends(get_db)):
    content = db.get(Content, contentId)
    if not content:
        api_error(404, "CONTENT_NOT_FOUND", "Contenido no encontrado.")
    job = index_content(db, user, content)
    return {"jobId": job.id, "estado": job.estado, "result": job.resultado}


@router.get("/contents/{contentId}/status")
def content_status(contentId: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    content = db.get(Content, contentId)
    if not content:
        api_error(404, "CONTENT_NOT_FOUND", "Contenido no encontrado.")
    can_access_course(db, user, content.curso_id)
    count = db.query(RAGFragment).filter(RAGFragment.contenido_id == content.id).count()
    return {"estado": content.estado_indexacion, "errorCode": "INDEX_ERROR" if content.estado_indexacion == "error" else None, "fragmentCount": count}


@router.get("/contents/{contentId}/download")
def download_content(contentId: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    content = db.get(Content, contentId)
    if not content:
        api_error(404, "CONTENT_NOT_FOUND", "Contenido no encontrado.")
    can_access_course(db, user, content.curso_id)
    try:
        path = get_storage().local_path(content.s3_key)
    except RuntimeError:
        api_error(503, "DOWNLOAD_ADAPTER_REQUIRED", "El adaptador S3 debe entregar URL prefirmada en despliegue AWS.")
    if not path.exists():
        api_error(404, "FILE_NOT_FOUND", "El archivo físico no está disponible.")
    return FileResponse(path, filename=content.nombre_original)


@router.get("/courses/{courseId}/contents")
def list_contents(courseId: str, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), user: User = Depends(current_user), db: Session = Depends(get_db)):
    can_access_course(db, user, courseId)
    q = db.query(Content).filter(Content.curso_id == courseId)
    total = q.count()
    rows = q.order_by(Content.creado_en.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"items": [content_json(c) for c in rows], "page": page, "total": total}


@router.get("/jobs/{jobId}")
def job_status(jobId: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    job = db.get(Job, jobId)
    if not job:
        api_error(404, "JOB_NOT_FOUND", "Trabajo no encontrado.")
    if user.rol != "administrador" and job.usuario_id != user.id:
        api_error(403, "FORBIDDEN", "Trabajo no autorizado.")
    return {"id": job.id, "estado": job.estado, "result": job.resultado, "errorCode": (job.resultado or {}).get("errorCode") if job.estado == "error" else None}
