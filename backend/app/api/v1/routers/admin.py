from __future__ import annotations

import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...deps import current_admin, current_user
from ....core.config import settings
from ....core.errors import api_error
from ....core.security import hash_password
from ....db.audit import audit
from ....db.session import get_db
from ....models import Audit, Config, RolePermission, User
from ....schemas import AdminUserIn, AdminUserPatch, ConfigPatch, RolePatch
from ....services.access import has_permission
from ....services.serializers import dtiso, user_json

router = APIRouter(prefix="/api/admin", tags=["Administración"])
ROLES = {"administrador", "docente", "estudiante"}


def _require_admin_permission(db: Session, user: User, permission: str):
    if user.rol != "administrador" or not has_permission(db, user, permission):
        api_error(403, "FORBIDDEN", f"Permiso administrativo requerido: {permission}.")


@router.get("/users")
def admin_users(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), rol: str | None = None, estado: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _require_admin_permission(db, user, "admin:users")
    q = db.query(User)
    if rol:
        q = q.filter(User.rol == rol)
    if estado:
        q = q.filter(User.estado == estado)
    total = q.count()
    rows = q.order_by(User.creado_en.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"items": [user_json(row) for row in rows], "page": page, "total": total}


@router.post("/users", status_code=201)
def create_admin_user(body: AdminUserIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _require_admin_permission(db, user, "admin:users")
    if body.rol not in ROLES:
        api_error(422, "ROLE_INVALID", "Rol inválido.")
    email = body.correo.strip().lower()
    if db.query(User).filter(func.lower(User.correo) == email).first():
        api_error(409, "EMAIL_EXISTS", "El correo ya existe.")
    temp = "Monda" + secrets.token_hex(4) + "!"
    created = User(rol=body.rol, nombre=body.nombre, correo=email, password_hash=hash_password(temp), estado="pendiente")
    db.add(created)
    db.flush()
    audit(db, user.id, "USER_CREATE", f"usuario:{created.id}")
    db.commit()
    result = user_json(created)
    if settings.demo_mode:
        result["temporaryPassword"] = temp
    return result


@router.patch("/users/{userId}")
def update_admin_user(userId: str, body: AdminUserPatch, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _require_admin_permission(db, user, "admin:users")
    target = db.get(User, userId)
    if not target:
        api_error(404, "USER_NOT_FOUND", "Usuario no encontrado.")
    if target.version != body.version:
        api_error(409, "VERSION_CONFLICT", "El usuario cambió. Recarga antes de guardar.")
    if target.rol == "administrador" and target.estado == "activo" and (body.estado == "inactivo" or (body.rol is not None and body.rol != "administrador")):
        active_admins = db.query(User).filter(User.rol == "administrador", User.estado == "activo").count()
        if active_admins <= 1:
            api_error(409, "LAST_ADMIN", "No se puede desactivar o degradar al último administrador activo.")
    if body.rol is not None:
        if body.rol not in ROLES:
            api_error(422, "ROLE_INVALID", "Rol inválido.")
        target.rol = body.rol
    if body.estado is not None:
        if body.estado not in {"activo", "inactivo", "pendiente"}:
            api_error(422, "STATE_INVALID", "Estado inválido.")
        target.estado = body.estado
    target.version += 1
    audit(db, user.id, "USER_UPDATE", f"usuario:{target.id}")
    db.commit()
    return user_json(target)


@router.get("/roles")
def get_roles(user: User = Depends(current_user), db: Session = Depends(get_db)):
    _require_admin_permission(db, user, "admin:roles")
    rows = db.query(RolePermission).all()
    grouped = {role: [] for role in ROLES}
    for row in rows:
        grouped.setdefault(row.rol, []).append(row.permiso)
    return {"roles": [{"rol": role, "permisos": sorted(perms), "version": max([x.version for x in rows if x.rol == role] or [1])} for role, perms in sorted(grouped.items())]}


@router.patch("/roles")
def patch_roles(body: RolePatch, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _require_admin_permission(db, user, "admin:roles")
    if body.rol not in ROLES:
        api_error(422, "ROLE_INVALID", "Rol inválido.")
    rows = db.query(RolePermission).filter(RolePermission.rol == body.rol).all()
    current_version = max([x.version for x in rows] or [1])
    if body.version != current_version:
        api_error(409, "VERSION_CONFLICT", "La matriz RBAC cambió. Recarga antes de guardar.")
    # Evita dejar al rol administrador sin permisos administrativos mínimos.
    if body.rol == "administrador" and "admin:roles" not in body.permisos:
        api_error(422, "ADMIN_ROLE_LOCKOUT", "El rol administrador debe conservar admin:roles.")
    db.query(RolePermission).filter(RolePermission.rol == body.rol).delete(synchronize_session=False)
    for permission in sorted(set(body.permisos)):
        db.add(RolePermission(rol=body.rol, permiso=permission, version=current_version + 1))
    audit(db, user.id, "ROLE_PERMISSIONS_UPDATE", f"rol:{body.rol}")
    db.commit()
    return {"rol": body.rol, "permisos": sorted(set(body.permisos)), "version": current_version + 1}


@router.get("/config")
def get_config(user: User = Depends(current_user), db: Session = Depends(get_db)):
    _require_admin_permission(db, user, "admin:config")
    row = db.get(Config, "rag")
    if not row:
        return {"topK": settings.rag_top_k, "umbral": settings.rag_similarity_threshold, "mode": settings.rag_mode, "modelo": settings.gemini_llm_model, "ollamaModel": settings.ollama_llm_model, "version": 1}
    return {**row.valor, "version": row.version}


@router.patch("/config")
def patch_config(body: ConfigPatch, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _require_admin_permission(db, user, "admin:config")
    if body.mode not in {"gemini", "ollama", "fallback", "auto"}:
        api_error(422, "RAG_MODE_INVALID", "mode debe ser gemini, ollama, fallback o auto.")
    row = db.get(Config, "rag")
    if row and row.version != body.version:
        api_error(409, "VERSION_CONFLICT", "La configuración cambió. Recarga antes de guardar.")
    value = {"topK": body.topK, "umbral": body.umbral, "mode": body.mode, "modelo": body.modelo, "ollamaModel": body.ollamaModel}
    if row is None:
        row = Config(clave="rag", valor=value, version=1, actualizado_por=user.id)
        db.add(row)
    else:
        row.valor = value
        row.version += 1
        row.actualizado_por = user.id
        row.actualizado_en = datetime.now(timezone.utc)
    audit(db, user.id, "CONFIG_UPDATE", "config:rag")
    db.commit()
    return {**row.valor, "version": row.version}


@router.get("/audit")
def get_audit(actor: str | None = None, desde: datetime | None = None, hasta: datetime | None = None, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), user: User = Depends(current_user), db: Session = Depends(get_db)):
    _require_admin_permission(db, user, "admin:audit")
    q = db.query(Audit)
    if actor:
        q = q.filter(Audit.actor_id == actor)
    if desde:
        q = q.filter(Audit.creado_en >= desde)
    if hasta:
        q = q.filter(Audit.creado_en <= hasta)
    total = q.count()
    rows = q.order_by(Audit.creado_en.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"items": [{"id": row.id, "actorId": row.actor_id, "accion": row.accion, "objeto": row.objeto, "resultado": row.resultado, "correlationId": row.correlation_id, "creadoEn": dtiso(row.creado_en)} for row in rows], "page": page, "total": total}
