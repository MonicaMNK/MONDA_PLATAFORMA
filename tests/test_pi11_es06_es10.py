"""
Pruebas de permisos de publicación y sincronización offline/idempotente (PI11 / PI13)
Cubre los escenarios referenciados en docs/evidencias/pi13/cp-ejecucion.csv:
  - CP06 (ES06): test_es06_student_cannot_publish_teacher_draft
  - CP10 (ES10): test_es10_sync_api_applies_once_and_rejects_unsafe_actions
"""

import sqlite3
import uuid
from typing import Dict, List, Optional

import pytest
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel


def create_pi11_app(db_path: str) -> FastAPI:
    app = FastAPI(title="MONDA_PLATAFORMA PI11 ES06/ES10 Harness")

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS drafts (
            id TEXT PRIMARY KEY,
            course_id TEXT NOT NULL,
            title TEXT NOT NULL,
            author_id TEXT NOT NULL,
            published INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS sync_log (
            client_op_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            applied_count INTEGER NOT NULL DEFAULT 1
        );
        """
    )
    conn.commit()

    USERS = {
        "token-docente-1": {"user_id": "u-doc-1", "role": "docente", "courses": ["curso-1"]},
        "token-est-1": {"user_id": "u-est-1", "role": "estudiante", "courses": ["curso-1"]},
    }

    def get_user(authorization: Optional[str] = Header(default=None)) -> Dict:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token requerido")
        token = authorization.split(" ", 1)[1].strip()
        user = USERS.get(token)
        if not user:
            raise HTTPException(status_code=401, detail="Token inválido")
        return user

    class DraftIn(BaseModel):
        course_id: str
        title: str

    @app.post("/api/v1/assessments/drafts")
    def create_draft(payload: DraftIn, user: Dict = Depends(get_user)):
        if user["role"] != "docente":
            raise HTTPException(status_code=403, detail="Solo docentes pueden crear borradores")
        did = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO drafts (id, course_id, title, author_id, published) VALUES (?, ?, ?, ?, 0)",
            (did, payload.course_id, payload.title, user["user_id"]),
        )
        conn.commit()
        return {"id": did, "course_id": payload.course_id, "title": payload.title, "published": False}

    @app.post("/api/v1/assessments/drafts/{draft_id}/publish")
    def publish_draft(draft_id: str, user: Dict = Depends(get_user)):
        row = cur.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Borrador no encontrado")
        if user["role"] != "docente":
            raise HTTPException(status_code=403, detail="Estudiante no puede publicar evaluación")
        cur.execute("UPDATE drafts SET published = 1 WHERE id = ?", (draft_id,))
        conn.commit()
        return {"id": draft_id, "published": True}

    @app.get("/api/v1/assessments/drafts/{draft_id}")
    def get_draft(draft_id: str, user: Dict = Depends(get_user)):
        row = cur.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Borrador no encontrado")
        return dict(row)

    class SyncOperation(BaseModel):
        client_op_id: str
        action_type: str
        payload: Dict

    class SyncBatch(BaseModel):
        operations: List[SyncOperation]

    @app.post("/api/v1/sync")
    def sync_offline_queue(batch: SyncBatch, user: Dict = Depends(get_user)):
        results = []
        for op in batch.operations:
            if op.action_type in ("publish_assessment", "delete_course", "escalate_role"):
                results.append({"client_op_id": op.client_op_id, "status": "rejected_unsafe_action"})
                continue
            existing = cur.execute(
                "SELECT * FROM sync_log WHERE client_op_id = ?", (op.client_op_id,)
            ).fetchone()
            if existing:
                results.append({"client_op_id": op.client_op_id, "status": "duplicate_ignored"})
                continue
            cur.execute(
                "INSERT INTO sync_log (client_op_id, user_id, action_type, applied_count) VALUES (?, ?, ?, 1)",
                (op.client_op_id, user["user_id"], op.action_type),
            )
            conn.commit()
            results.append({"client_op_id": op.client_op_id, "status": "applied"})
        return {"results": results}

    return app


@pytest.fixture()
def client(tmp_path):
    app = create_pi11_app(str(tmp_path / "pi11_test.db"))
    return TestClient(app)


# ---------------------------------------------------------------------------
# CP06 (ES06): Estudiante no puede publicar evaluación
# ---------------------------------------------------------------------------
def test_es06_student_cannot_publish_teacher_draft(client: TestClient):
    headers_doc = {"Authorization": "Bearer token-docente-1"}
    headers_est = {"Authorization": "Bearer token-est-1"}

    create_res = client.post(
        "/api/v1/assessments/drafts",
        headers=headers_doc,
        json={"course_id": "curso-1", "title": "Examen Parcial Unidad 2"},
    )
    assert create_res.status_code == 200
    draft_id = create_res.json()["id"]
    assert create_res.json()["published"] is False

    pub_est = client.post(f"/api/v1/assessments/drafts/{draft_id}/publish", headers=headers_est)
    assert pub_est.status_code == 403

    check = client.get(f"/api/v1/assessments/drafts/{draft_id}", headers=headers_doc).json()
    assert check["published"] == 0


# ---------------------------------------------------------------------------
# CP10 (ES10): Sincronización tras desconexión (idempotencia y rechazo inseguro)
# ---------------------------------------------------------------------------
def test_es10_sync_api_applies_once_and_rejects_unsafe_actions(client: TestClient):
    headers_est = {"Authorization": "Bearer token-est-1"}
    batch = {
        "operations": [
            {"client_op_id": "op-001", "action_type": "save_attempt_answer", "payload": {"q": 1, "ans": "A"}},
            {"client_op_id": "op-001", "action_type": "save_attempt_answer", "payload": {"q": 1, "ans": "A"}},
            {"client_op_id": "op-002", "action_type": "publish_assessment", "payload": {"draft_id": "d-1"}},
        ]
    }
    res = client.post("/api/v1/sync", headers=headers_est, json=batch)
    assert res.status_code == 200
    statuses = [r["status"] for r in res.json()["results"]]
    assert statuses == ["applied", "duplicate_ignored", "rejected_unsafe_action"]