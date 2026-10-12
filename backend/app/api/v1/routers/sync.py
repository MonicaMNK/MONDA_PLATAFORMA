from __future__ import annotations

import hashlib
import json
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...deps import current_user
from ....db.audit import audit
from ....db.session import get_db
from ....models import Draft, SyncAction, User
from ....schemas import SyncIn

router = APIRouter(tags=["Sincronización"])
ALLOWED = {"borrador_personal", "valoracion"}

@router.post("/api/sync")
def sync(body: SyncIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    results = []
    for action in body.actions:
        try:
            action_id = str(uuid.UUID(action.actionId))
        except Exception:
            results.append({"actionId": action.actionId, "status": "rejected", "result": {"code": "ACTION_ID_INVALID"}})
            continue
        payload_bytes = json.dumps(action.payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()
        old = db.get(SyncAction, {"usuario_id": user.id, "accion_id": action_id})
        if old:
            if old.payload_hash != payload_hash:
                results.append({"actionId": action_id, "status": "conflict", "result": {"code": "IDEMPOTENCY_CONFLICT"}})
            else:
                results.append({"actionId": action_id, "status": "repeated", "result": old.resultado})
            continue
        if action.tipo not in ALLOWED:
            result = {"code": "OFFLINE_ACTION_NOT_ALLOWED", "tipo": action.tipo}
            db.add(SyncAction(usuario_id=user.id, accion_id=action_id, payload_hash=payload_hash, resultado=result))
            results.append({"actionId": action_id, "status": "rejected", "result": result})
            continue
        course_id = action.payload.get("courseId")
        draft = Draft(usuario_id=user.id, curso_id=course_id, tipo=action.tipo, payload=action.payload, base_version=action.version, accion_id=action_id, sincronizado=True)
        db.add(draft)
        db.flush()
        result = {"draftId": draft.id, "tipo": action.tipo, "applied": True, "version": action.version}
        db.add(SyncAction(usuario_id=user.id, accion_id=action_id, payload_hash=payload_hash, resultado=result))
        results.append({"actionId": action_id, "status": "applied", "result": result})
    audit(db, user.id, "SYNC_BATCH", f"acciones:{len(body.actions)}")
    db.commit()
    return {"results": results}
