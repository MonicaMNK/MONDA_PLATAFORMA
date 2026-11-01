from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...deps import authenticated_user
from ....core.errors import api_error
from ....db.audit import audit
from ....db.session import get_db
from ....models import Audit, User
from ...legal import CONTENT_SHARING_TERMS, PLATFORM_TERMS, PLATFORM_TERMS_VERSION

router = APIRouter(prefix="/api/legal", tags=["Condiciones de uso"])


class TermsAcceptanceIn(BaseModel):
    version: str = Field(min_length=1, max_length=40)
    accepted: bool


@router.get("/terms")
def get_terms(user: User = Depends(authenticated_user)):
    return {**PLATFORM_TERMS, "role": user.rol}


@router.get("/content-sharing")
def get_content_sharing_terms(user: User = Depends(authenticated_user)):
    if user.rol not in {"administrador", "docente"}:
        return {"version": CONTENT_SHARING_TERMS["version"], "title": CONTENT_SHARING_TERMS["title"], "items": []}
    return CONTENT_SHARING_TERMS


@router.post("/terms/accept")
def accept_terms(body: TermsAcceptanceIn, request: Request, user: User = Depends(authenticated_user), db: Session = Depends(get_db)):
    if body.version != PLATFORM_TERMS_VERSION:
        api_error(409, "TERMS_VERSION_CHANGED", "Las condiciones cambiaron. Vuelve a leer la versión vigente.", request=request)
    if not body.accepted:
        api_error(422, "TERMS_NOT_ACCEPTED", "Debes aceptar las condiciones para continuar.", request=request)
    existing = db.query(Audit).filter_by(
        actor_id=user.id, accion="PLATFORM_TERMS_ACCEPT", objeto=f"version:{PLATFORM_TERMS_VERSION}"
    ).first()
    if existing is None:
        audit(db, user.id, "PLATFORM_TERMS_ACCEPT", f"version:{PLATFORM_TERMS_VERSION}")
        db.commit()
    return {"accepted": True, "version": PLATFORM_TERMS_VERSION}
