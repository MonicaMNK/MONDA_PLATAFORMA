from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from .config import settings

try:
    import bcrypt  # type: ignore
except Exception:  # pragma: no cover - only used in dependency-missing test environments
    bcrypt = None


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    if bcrypt is not None:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")
    if not settings.allow_test_password_fallback:
        raise RuntimeError("bcrypt no está instalado. Ejecute: pip install -r requirements.txt")
    salt = secrets.token_bytes(16)
    rounds = 240_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, rounds)
    b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")
    return f"pbkdf2_test${rounds}${b64(salt)}${b64(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    if encoded.startswith(("$2a$", "$2b$", "$2y$")):
        return bool(bcrypt and bcrypt.checkpw(password.encode("utf-8"), encoded.encode("ascii")))
    if encoded.startswith("pbkdf2_test$") and settings.allow_test_password_fallback:
        try:
            _, rounds, salt_s, digest_s = encoded.split("$", 3)
            unb64 = lambda s: base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
            got = hashlib.pbkdf2_hmac("sha256", password.encode(), unb64(salt_s), int(rounds))
            return hmac.compare_digest(got, unb64(digest_s))
        except Exception:
            return False
    return False


def create_access_token(user_id: str, role: str) -> str:
    now = utcnow()
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_minutes)).timestamp()),
        "iss": "monda-local",
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"], issuer="monda-local")


def new_refresh_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(48)
    return raw, token_hash(raw)


def token_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def refresh_expiration() -> datetime:
    return utcnow() + timedelta(days=settings.refresh_days)


def recovery_expiration() -> datetime:
    return utcnow() + timedelta(minutes=15)
