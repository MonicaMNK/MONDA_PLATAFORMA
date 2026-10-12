from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, Header, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID

from ...deps import current_user
from ....core.errors import api_error
from ....core.config import settings
from ....db.session import get_db
from ....models import Content, ContentFolder, Event, Job, RAGFragment, User
from ....services.access import can_access_course, teacher_course
from ....schemas.api import FolderIn, FolderPatch, ContentFolderPatch
from ....db.audit import audit
from ....rag import extract_text
from ....services.content_service import create_content, index_content
from ....services.serializers import content_json
from ....services.storage import get_storage

router = APIRouter(prefix="/api", tags=["Contenidos"])


@router.post("/courses/{courseId}/contents", status_code=201)
async def upload_content(courseId: str, file: UploadFile = File(...), documentoId: str | None = Form(None), version: int = Form(1), folderId: str | None = Form(None), user: User = Depends(current_user), db: Session = Depends(get_db)):
    can_access_course(db, user, courseId, write=True)
    data = await file.read(settings.max_upload_bytes + 1)
    content = create_content(db, user, courseId, file.filename or "material", file.content_type, data, documentoId, version, folderId)
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
    db.add(Event(usuario_seudonimo=user.seudonimo,curso_id=content.curso_id,tipo='material_download'))
    db.commit()
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


def folder_json(folder: ContentFolder):
    return {"id": folder.id, "courseId": folder.curso_id, "parentId": folder.padre_id, "nombre": folder.nombre}


def folder_name(name: str):
    name = name.strip()
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        api_error(422, "FOLDER_NAME_INVALID", "Escribe un nombre de carpeta sin barras.")
    return name


@router.get("/courses/{courseId}/folders")
def list_folders(courseId: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    can_access_course(db, user, courseId)
    rows = db.query(ContentFolder).filter(ContentFolder.curso_id == courseId).order_by(ContentFolder.nombre).all()
    return {"items": [folder_json(f) for f in rows]}


@router.post("/courses/{courseId}/folders", status_code=201)
def create_folder(courseId: str, body: FolderIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    teacher_course(db, user, courseId)
    parent_id = str(body.parentId) if body.parentId else None
    if parent_id:
        parent = db.get(ContentFolder, parent_id)
        if not parent or parent.curso_id != courseId:
            api_error(403, "FOLDER_FORBIDDEN", "La carpeta padre no pertenece al curso.")
    name = folder_name(body.nombre)
    if db.query(ContentFolder).filter(ContentFolder.curso_id == courseId, ContentFolder.padre_id == parent_id, func.lower(ContentFolder.nombre) == name.lower()).first():
        api_error(409, "FOLDER_EXISTS", "Ya existe una carpeta con ese nombre aquí.")
    row = ContentFolder(curso_id=courseId, padre_id=parent_id, nombre=name, creado_por=user.id)
    db.add(row)
    db.flush()
    audit(db, user.id, "FOLDER_CREATE", f"carpeta:{row.id}")
    db.commit()
    return folder_json(row)


@router.patch("/folders/{folderId}")
def rename_folder(folderId: UUID, body: FolderPatch, user: User = Depends(current_user), db: Session = Depends(get_db)):
    folder = db.get(ContentFolder, str(folderId))
    if not folder:
        api_error(404, "FOLDER_NOT_FOUND", "Carpeta no encontrada.")
    teacher_course(db, user, folder.curso_id)
    name = folder_name(body.nombre)
    if db.query(ContentFolder).filter(ContentFolder.curso_id == folder.curso_id, ContentFolder.padre_id == folder.padre_id, ContentFolder.id != folder.id, func.lower(ContentFolder.nombre) == name.lower()).first():
        api_error(409, "FOLDER_EXISTS", "Ya existe una carpeta con ese nombre aquí.")
    folder.nombre = name
    audit(db, user.id, "FOLDER_RENAME", f"carpeta:{folder.id}")
    db.commit()
    return folder_json(folder)


@router.patch("/contents/{contentId}/folder")
def move_content(contentId: UUID, body: ContentFolderPatch, user: User = Depends(current_user), db: Session = Depends(get_db)):
    content = db.get(Content, str(contentId))
    if not content:
        api_error(404, "CONTENT_NOT_FOUND", "Material no encontrado.")
    teacher_course(db, user, content.curso_id)
    folder_id = str(body.folderId) if body.folderId else None
    if folder_id:
        folder = db.get(ContentFolder, folder_id)
        if not folder or folder.curso_id != content.curso_id:
            api_error(403, "FOLDER_FORBIDDEN", "La carpeta no pertenece a este curso.")
    content.carpeta_id = folder_id
    audit(db, user.id, "CONTENT_MOVE", f"contenido:{content.id}")
    db.commit()
    return content_json(content)


@router.get("/contents/{contentId}/preview")
def preview_content(contentId: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    content = db.get(Content, str(contentId))
    if not content:
        api_error(404, "CONTENT_NOT_FOUND", "Material no encontrado.")
    can_access_course(db, user, content.curso_id)
    path = get_storage().local_path(content.s3_key)
    if not path.exists():
        api_error(404, "FILE_NOT_FOUND", "Archivo no disponible.")
    try:
        text, _ = extract_text(path)
    except Exception:
        api_error(422, "PREVIEW_UNAVAILABLE", "No se puede extraer texto; descarga el archivo para abrirlo.")
    db.add(Event(usuario_seudonimo=user.seudonimo,curso_id=content.curso_id,tipo='material_view'))
    db.commit()
    return {"nombre": content.nombre_original, "text": text[:50000], "truncated": len(text) > 50000}
