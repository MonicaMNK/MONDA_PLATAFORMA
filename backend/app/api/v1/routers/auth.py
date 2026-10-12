from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy.orm import Session

from ...deps import current_user
from ....core.config import settings
from ....core.errors import api_error
from ....db.session import get_db
from ....schemas import LoginIn, RecoveryIn, ResetIn
from ....services.auth_service import login, logout_family, request_recovery, reset_password, rotate_refresh
from ....services.serializers import user_json

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


def _set_cookies(response: Response, refresh: str, csrf: str | None = None) -> None:
    response.set_cookie("monda_refresh", refresh, httponly=True, secure=settings.cookie_secure, samesite="strict", max_age=settings.refresh_days * 86400, path="/api/auth")
    if csrf is not None:
        response.set_cookie("monda_csrf", csrf, httponly=False, secure=settings.cookie_secure, samesite="strict", max_age=settings.refresh_days * 86400, path="/api/auth")


@router.post("/login")
def login_endpoint(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    user, access, refresh, csrf = login(db, body.correo, body.password, request.state.correlation_id)
    _set_cookies(response, refresh, csrf)
    return {"accessToken": access, "expiresIn": settings.access_minutes * 60, "csrfToken": csrf, "user": user_json(user)}


@router.post("/refresh")
def refresh_endpoint(request: Request, response: Response, x_csrf_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    raw = request.cookies.get("monda_refresh")
    csrf = request.cookies.get("monda_csrf")
    if not raw or not csrf or x_csrf_token != csrf:
        api_error(403, "CSRF_INVALID", "CSRF inválido.")
    user, access, new_refresh = rotate_refresh(db, raw, request.state.correlation_id)
    _set_cookies(response, new_refresh)
    return {"accessToken": access, "expiresIn": settings.access_minutes * 60}


@router.post("/logout", status_code=204)
def logout_endpoint(request: Request, response: Response, x_csrf_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    raw = request.cookies.get("monda_refresh")
    csrf = request.cookies.get("monda_csrf")
    if raw and csrf and x_csrf_token != csrf:
        api_error(403, "CSRF_INVALID", "CSRF inválido.")
    logout_family(db, raw, None, request.state.correlation_id)
    response.delete_cookie("monda_refresh", path="/api/auth")
    response.delete_cookie("monda_csrf", path="/api/auth")


@router.post("/recovery", status_code=202)
def recovery_endpoint(body: RecoveryIn, request: Request, db: Session = Depends(get_db)):
    raw = request_recovery(db, body.correo, request.state.correlation_id)
    result = {"message": "Si la cuenta existe, se generó un enlace de recuperación válido por 15 minutos."}
    if settings.demo_mode and raw:
        result["demoToken"] = raw
    return result


@router.post("/reset", status_code=204)
def reset_endpoint(body: ResetIn, request: Request, db: Session = Depends(get_db)):
    reset_password(db, body.token, body.password, request.state.correlation_id)
