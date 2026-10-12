from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import Audit, uid


def audit(db: Session, actor_id: str | None, action: str, obj: str, result: str = "ok", correlation_id: str | None = None) -> Audit:
    row = Audit(actor_id=actor_id, accion=action, objeto=obj, resultado=result, correlation_id=correlation_id or uid())
    db.add(row)
    return row
