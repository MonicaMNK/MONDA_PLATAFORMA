from __future__ import annotations

import secrets
import threading
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.errors import api_error
from ..core.security import create_access_token, hash_password, new_refresh_token, recovery_expiration, refresh_expiration, token_hash, utcnow, verify_password
from ..db.audit import audit
from ..models import Recovery, SessionToken, User, uid

_lock = threading.Lock()
_failures: dict[str, list[datetime]] = {}


def _login_allowed(email: str) -> bool:
    cutoff = utcnow() - timedelta(minutes=settings.login_lock_minutes)
    with _lock:
        recent = [x for x in _failures.get(email, []) if x >= cutoff]
        _failures[email] = recent
        return len(recent) < settings.login_max_failures


def _record_failure(email: str) -> None:
    with _lock:
        _failures.setdefault(email, []).append(utcnow())


def _clear_failures(email: str) -> None:
    with _lock:
        _failures.pop(email, None)


def login(db: Session, correo: str, password: str, correlation_id: str) -> tuple[User, str, str, str]:
    email = correo.strip().lower()
    if not _login_allowed(email):
        audit(db, None, "AUTH_LOGIN", f"correo_hash:{token_hash(email)[:16]}", result="rate_limited", correlation_id=correlation_id)
        db.commit()
        api_error(429, "LOGIN_RATE_LIMIT", "Demasiados intentos fallidos. Intenta nuevamente más tarde.")
    user = db.query(User).filter(func.lower(User.correo) == email).first()
    if not user or user.estado != "activo" or not verify_password(password, user.password_hash):
        _record_failure(email)
        audit(db, user.id if user else None, "AUTH_LOGIN", f"correo_hash:{token_hash(email)[:16]}", result="denied", correlation_id=correlation_id)
        db.commit()
        api_error(401, "LOGIN_FAILED", "Correo o contraseña incorrectos.")
    _clear_failures(email)
    raw, hashed = new_refresh_token()
    family = uid()
    db.add(SessionToken(usuario_id=user.id, familia_id=family, token_hash=hashed, expira_en=refresh_expiration()))
    audit(db, user.id, "AUTH_LOGIN", f"usuario:{user.id}", correlation_id=correlation_id)
    db.commit()
    csrf = secrets.token_urlsafe(24)
    return user, create_access_token(user.id, user.rol), raw, csrf


def rotate_refresh(db: Session, raw: str, correlation_id: str) -> tuple[User, str, str]:
    session = db.query(SessionToken).filter(SessionToken.token_hash == token_hash(raw)).first()
    if not session:
        api_error(401, "REFRESH_INVALID", "Refresh token inválido.")
    if session.revocada:
        db.query(SessionToken).filter(SessionToken.familia_id == session.familia_id).update({"revocada": True}, synchronize_session=False)
        audit(db, session.usuario_id, "REFRESH_REUSE", f"familia:{session.familia_id}", result="revoked", correlation_id=correlation_id)
        db.commit()
        api_error(401, "REFRESH_REUSED", "Se detectó reutilización del refresh token; la familia fue revocada.")
    exp = session.expira_en if session.expira_en.tzinfo else session.expira_en.replace(tzinfo=timezone.utc)
    if exp <= utcnow():
        session.revocada = True
        db.commit()
        api_error(401, "REFRESH_EXPIRED", "Refresh token expirado.")
    user = db.get(User, session.usuario_id)
    if not user or user.estado != "activo":
        api_error(401, "AUTH_INACTIVE", "Usuario inactivo o inexistente.")
    session.revocada = True
    new_raw, new_hash = new_refresh_token()
    db.add(SessionToken(usuario_id=user.id, familia_id=session.familia_id, token_hash=new_hash, expira_en=refresh_expiration()))
    db.commit()
    return user, create_access_token(user.id, user.rol), new_raw


def logout_family(db: Session, raw: str | None, actor_id: str | None, correlation_id: str) -> None:
    if raw:
        session = db.query(SessionToken).filter(SessionToken.token_hash == token_hash(raw)).first()
        if session:
            db.query(SessionToken).filter(SessionToken.familia_id == session.familia_id).update({"revocada": True}, synchronize_session=False)
    audit(db, actor_id, "AUTH_LOGOUT", f"usuario:{actor_id or 'unknown'}", correlation_id=correlation_id)
    db.commit()


def request_recovery(db: Session, correo: str, correlation_id: str) -> str | None:
    user = db.query(User).filter(func.lower(User.correo) == correo.strip().lower()).first()
    raw = None
    if user:
        raw = secrets.token_urlsafe(36)
        db.add(Recovery(usuario_id=user.id, token_hash=token_hash(raw), expira_en=recovery_expiration()))
        audit(db, user.id, "PASSWORD_RECOVERY_REQUEST", f"usuario:{user.id}", correlation_id=correlation_id)
        db.commit()
    return raw


def reset_password(db: Session, token: str, new_password: str, correlation_id: str) -> None:
    recovery = db.query(Recovery).filter(Recovery.token_hash == token_hash(token)).first()
    if not recovery or recovery.usado_en is not None:
        api_error(400, "RESET_INVALID", "Token inválido o ya utilizado.")
    exp = recovery.expira_en if recovery.expira_en.tzinfo else recovery.expira_en.replace(tzinfo=timezone.utc)
    if exp <= utcnow():
        api_error(400, "RESET_EXPIRED", "Token expirado.")
    user = db.get(User, recovery.usuario_id)
    user.password_hash = hash_password(new_password)
    recovery.usado_en = utcnow()
    db.query(SessionToken).filter(SessionToken.usuario_id == user.id).update({"revocada": True}, synchronize_session=False)
    audit(db, user.id, "PASSWORD_RESET", f"usuario:{user.id}", correlation_id=correlation_id)
    db.commit()
