from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..core.errors import api_error
from ..core.security import decode_access_token
from ..db.session import get_db
from ..models import User
from ..services.access import has_permission

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="JWTBearer", description="Access token JWT HS256 de 30 minutos")


def current_user(
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


def current_admin(user: User = Depends(current_user), db: Session = Depends(get_db)) -> User:
    if user.rol != "administrador" or not has_permission(db, user, "admin:users"):
        api_error(403, "FORBIDDEN", "Se requiere rol Administrador.")
    return user
