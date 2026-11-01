from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..core.errors import api_error
from ..core.security import decode_access_token
from ..db.session import get_db
from ..models import Audit, User
from ..services.access import has_permission

from .legal import PLATFORM_TERMS_VERSION

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="JWTBearer", description="Access token JWT HS256 de 30 minutos")


def authenticated_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        api_error(401, "AUTH_REQUIRED", "Se requiere una sesión válida.", request=request)
    try:
        payload = decode_access_token(credentials.credentials)
    except Exception:
        api_error(401, "AUTH_INVALID", "La sesión expiró o no es válida.", request=request)
    user = db.get(User, payload.get("sub"))
    if not user or user.estado != "activo":
        api_error(401, "AUTH_INACTIVE", "Usuario inactivo o inexistente.", request=request)
    return user


def current_user(
    request: Request,
    user: User = Depends(authenticated_user),
    db: Session = Depends(get_db),
) -> User:
    accepted = db.query(Audit.id).filter(
        Audit.actor_id == user.id,
        Audit.accion == "PLATFORM_TERMS_ACCEPT",
        Audit.objeto == f"version:{PLATFORM_TERMS_VERSION}",
    ).first()
    if not accepted:
        api_error(428, "TERMS_ACCEPTANCE_REQUIRED", "Debes revisar y aceptar las condiciones de uso antes de continuar.", request=request)
    return user


def current_admin(user: User = Depends(current_user), db: Session = Depends(get_db)) -> User:
    if user.rol != "administrador" or not has_permission(db, user, "admin:users"):
        api_error(403, "FORBIDDEN", "Se requiere rol Administrador.")
    return user
