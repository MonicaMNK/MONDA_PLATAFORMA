"""PI11/PI12: negative publication and synchronization API evidence.

These tests exercise the real FastAPI routes with synthetic accounts. The
sync test models a queued request after reconnection; it does not claim to
exercise a browser service worker or offline UI.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.db.seed import init_test_db
from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models import Assessment, Draft, SyncAction


def _auth(client: TestClient, role: str) -> dict[str, str]:
    email, password = {
        "teacher": ("docente@monda.local", "Docente123!"),
        "student": ("estudiante@monda.local", "Estudiante123!"),
    }[role]
    response = client.post("/api/auth/login", json={"correo": email, "password": password})
    assert response.status_code == 200, response.text
    headers = {"Authorization": f"Bearer {response.json()['accessToken']}"}
    if not response.json().get("legalTermsAccepted"):
        accepted = client.post(
            "/api/legal/terms/accept",
            headers=headers,
            json={"version": "2026-10-v1", "accepted": True},
        )
        assert accepted.status_code == 200, accepted.text
    return headers


def test_es06_student_cannot_publish_teacher_draft():
    init_test_db(True)
    with TestClient(app) as client:
        teacher = _auth(client, "teacher")
        student = _auth(client, "student")
        courses = client.get("/api/courses", headers=teacher)
        assert courses.status_code == 200
        course_id = courses.json()["items"][0]["id"]
        generated = client.post(
            f"/api/courses/{course_id}/assessments/generate",
            headers=teacher,
            json={"tema": "Prueba de autorización sintética", "cantidad": 2},
        )
        assert generated.status_code == 202, generated.text
        assessment_id = generated.json()["assessmentId"]
        before = client.get(f"/api/assessments/{assessment_id}", headers=teacher).json()
        assert before["estado"] == "borrador"
        now = datetime.now(timezone.utc)
        denied = client.post(
            f"/api/assessments/{assessment_id}/publish",
            headers=student,
            json={
                "fechaInicio": now.isoformat(),
                "fechaFin": (now + timedelta(days=1)).isoformat(),
                "version": before["version"],
            },
        )
        assert denied.status_code == 403, denied.text
        assert denied.json()["code"] in {"FORBIDDEN", "COURSE_FORBIDDEN"}
        after = client.get(f"/api/assessments/{assessment_id}", headers=teacher).json()
        assert (after["estado"], after["version"]) == (before["estado"], before["version"])
        with SessionLocal() as db:
            assert db.get(Assessment, assessment_id).estado == "borrador"
        print(f"ES06: HTTP {denied.status_code} {denied.json()['code']}; estado antes/despues: borrador; version sin cambios")


def test_es10_sync_api_applies_once_and_rejects_unsafe_actions():
    init_test_db(True)
    with TestClient(app) as client:
        student = _auth(client, "student")
        courses = client.get("/api/courses", headers=student)
        assert courses.status_code == 200
        course_id = courses.json()["items"][0]["id"]
        action_id = str(uuid4())
        action = {
            "actionId": action_id,
            "tipo": "borrador_personal",
            "version": 1,
            "payload": {"courseId": course_id, "text": "Nota sintética guardada sin conexión"},
        }
        # The same queued action is sent after reconnection and retried.
        first = client.post("/api/sync", headers=student, json={"actions": [action]})
        assert first.status_code == 200, first.text
        first_result = first.json()["results"][0]
        assert first_result["status"] == "applied"
        draft_id = first_result["result"]["draftId"]
        repeated = client.post("/api/sync", headers=student, json={"actions": [action]})
        assert repeated.status_code == 200
        assert repeated.json()["results"][0]["status"] == "repeated"
        assert repeated.json()["results"][0]["result"]["draftId"] == draft_id
        changed = {**action, "payload": {"courseId": course_id, "text": "Cambio no autorizado del mismo actionId"}}
        conflict = client.post("/api/sync", headers=student, json={"actions": [changed]})
        assert conflict.status_code == 200
        assert conflict.json()["results"][0] == {
            "actionId": action_id,
            "status": "conflict",
            "result": {"code": "IDEMPOTENCY_CONFLICT"},
        }
        unsafe = client.post(
            "/api/sync",
            headers=student,
            json={"actions": [{"actionId": str(uuid4()), "tipo": "assessment_submit", "version": 1, "payload": {"courseId": course_id}}]},
        )
        assert unsafe.status_code == 200
        assert unsafe.json()["results"][0]["status"] == "rejected"
        assert unsafe.json()["results"][0]["result"]["code"] == "OFFLINE_ACTION_NOT_ALLOWED"
        with SessionLocal() as db:
            assert db.query(Draft).filter_by(accion_id=action_id).count() == 1
            assert db.query(SyncAction).filter_by(accion_id=action_id).count() == 1
        print("ES10 API: applied, repeated, conflict; assessment_submit rejected; 1 borrador y 1 accion persistidos")
