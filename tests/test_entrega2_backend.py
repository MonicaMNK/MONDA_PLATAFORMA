from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from backend.app.db.seed import init_test_db
from backend.app.main import app


def auth(client: TestClient, email: str, password: str):
    response = client.post("/api/auth/login", json={"correo": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["accessToken"]}


def test_full_pi7_backend_flow_fallback_rag():
    init_test_db(True)
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        teacher = auth(client, "docente@monda.local", "Docente123!")
        courses = client.get("/api/courses", headers=teacher)
        assert courses.status_code == 200
        course_id = courses.json()["items"][0]["id"]

        # RAG fallback: consulta solo material autorizado y devuelve fuentes.
        rag = client.post(f"/api/courses/{course_id}/rag/query", headers=teacher, json={"question": "¿Qué es un sistema?"})
        assert rag.status_code == 200, rag.text
        assert rag.json()["mode"] == "fallback"
        assert rag.json()["evidenceSufficient"] is True
        assert rag.json()["sources"]

        # Generación -> revisión humana obligatoria -> publicación.
        generated = client.post(
            f"/api/courses/{course_id}/assessments/generate",
            headers=teacher,
            json={"tema": "Sistemas", "bloom": "comprender", "dificultad": "media", "cantidad": 2, "tipo": "opcion_multiple"},
        )
        assert generated.status_code == 202, generated.text
        assessment_id = generated.json()["assessmentId"]
        detail = client.get(f"/api/assessments/{assessment_id}", headers=teacher).json()
        assert len(detail["questions"]) == 2

        start = datetime.now(timezone.utc) - timedelta(minutes=1)
        end = datetime.now(timezone.utc) + timedelta(days=7)
        blocked = client.post(
            f"/api/assessments/{assessment_id}/publish",
            headers=teacher,
            json={"fechaInicio": start.isoformat(), "fechaFin": end.isoformat(), "version": detail["version"]},
        )
        assert blocked.status_code == 409
        assert blocked.json()["code"] == "REVIEW_REQUIRED"

        for question in detail["questions"]:
            reviewed = client.patch(
                f"/api/questions/{question['id']}/review",
                headers=teacher,
                json={"estado": "aprobado", "version": question["version"]},
            )
            assert reviewed.status_code == 200, reviewed.text

        detail = client.get(f"/api/assessments/{assessment_id}", headers=teacher).json()
        published = client.post(
            f"/api/assessments/{assessment_id}/publish",
            headers=teacher,
            json={"fechaInicio": start.isoformat(), "fechaFin": end.isoformat(), "version": detail["version"]},
        )
        assert published.status_code == 200, published.text

        student = auth(client, "estudiante@monda.local", "Estudiante123!")
        student_detail = client.get(f"/api/assessments/{assessment_id}", headers=student)
        assert student_detail.status_code == 200
        assert "clave" not in student_detail.json()["questions"][0]
        assert "justificacion" not in student_detail.json()["questions"][0]

        started = client.post(
            f"/api/assessments/{assessment_id}/attempts",
            headers={**student, "Idempotency-Key": "start-1"},
            json={"accion": "iniciar"},
        )
        assert started.status_code == 200, started.text
        answers = {q["id"]: "A" for q in student_detail.json()["questions"]}
        closed = client.post(
            f"/api/assessments/{assessment_id}/attempts",
            headers={**student, "Idempotency-Key": "close-1"},
            json={"accion": "cerrar", "intentoId": started.json()["attemptId"], "respuestas": answers},
        )
        assert closed.status_code == 200, closed.text
        assert closed.json()["puntaje"] is None
        assert closed.json()["resultsPublished"] is False
        # Reenvío no duplica calificación.
        repeated = client.post(
            f"/api/assessments/{assessment_id}/attempts",
            headers={**student, "Idempotency-Key": "close-1"},
            json={"accion": "cerrar", "intentoId": started.json()["attemptId"], "respuestas": answers},
        )
        assert repeated.status_code == 200
        assert repeated.json()["puntaje"] is None
        current=client.get(f'/api/assessments/{assessment_id}',headers=teacher).json()
        released=client.post(f'/api/assessments/{assessment_id}/results/publish',headers=teacher,json={'version':current['version']})
        assert released.status_code==200,released.text
        result=client.get(f'/api/assessments/{assessment_id}/results',headers=student)
        assert result.status_code==200
        assert result.json()['puntaje']==20.0

        admin = auth(client, "admin@monda.local", "Admin123!")
        assert client.get("/api/admin/users", headers=admin).status_code == 200
        assert client.get("/api/admin/config", headers=admin).status_code == 200
        assert client.get("/api/admin/audit", headers=admin).status_code == 200


def test_course_isolation_and_rbac():
    init_test_db(True)
    with TestClient(app) as client:
        student = auth(client, "estudiante@monda.local", "Estudiante123!")
        assert client.post("/api/courses", headers=student, json={"nombre": "No permitido"}).status_code == 403
        assert client.get("/api/admin/users", headers=student).status_code == 403

        teacher = auth(client, "docente@monda.local", "Docente123!")
        course_id = client.get("/api/courses", headers=teacher).json()["items"][0]["id"]
        enrollments = client.get(f"/api/courses/{course_id}/enrollments", headers=teacher)
        assert enrollments.status_code == 200
        assert enrollments.json()["total"] == 1


def test_sync_idempotency_and_rejects_assessment_offline():
    init_test_db(True)
    with TestClient(app) as client:
        student = auth(client, "estudiante@monda.local", "Estudiante123!")
        action_id = "11111111-1111-4111-8111-111111111111"
        payload = {"actions": [{"actionId": action_id, "tipo": "borrador_personal", "payload": {"text": "nota local"}, "version": 1}]}
        first = client.post("/api/sync", headers=student, json=payload)
        second = client.post("/api/sync", headers=student, json=payload)
        assert first.json()["results"][0]["status"] == "applied"
        assert second.json()["results"][0]["status"] == "repeated"

        forbidden = client.post(
            "/api/sync",
            headers=student,
            json={"actions": [{"actionId": "22222222-2222-4222-8222-222222222222", "tipo": "assessment_submit", "payload": {}, "version": 1}]},
        )
        assert forbidden.status_code == 200
        assert forbidden.json()["results"][0]["status"] == "rejected"


def test_material_upload_version_and_index_fallback():
    from io import BytesIO
    from docx import Document

    init_test_db(True)
    with TestClient(app) as client:
        teacher = auth(client, "docente@monda.local", "Docente123!")
        course_id = client.get("/api/courses", headers=teacher).json()["items"][0]["id"]

        doc = Document()
        doc.add_paragraph("La arquitectura MVC separa modelo, vista y controlador para reducir acoplamiento y facilitar el mantenimiento.")
        buf = BytesIO()
        doc.save(buf)
        upload = client.post(
            f"/api/courses/{course_id}/contents",
            headers=teacher,
            files={"file": ("mvc.docx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"version": "1"},
        )
        assert upload.status_code == 201, upload.text
        content_id = upload.json()["contentId"]
        indexed = client.post(f"/api/contents/{content_id}/index", headers={**teacher, "Idempotency-Key": "idx-mvc"})
        assert indexed.status_code == 202, indexed.text
        assert indexed.json()["estado"] == "completado"
        status = client.get(f"/api/contents/{content_id}/status", headers=teacher)
        assert status.json()["estado"] == "indexado"
        assert status.json()["fragmentCount"] >= 1

        rag = client.post(f"/api/courses/{course_id}/rag/query", headers=teacher, json={"question": "¿Qué separa la arquitectura MVC?"})
        assert rag.status_code == 200
        assert any(source["contentId"] == content_id for source in rag.json()["sources"])


def test_refresh_rotation_requires_csrf():
    init_test_db(True)
    with TestClient(app) as client:
        login = client.post('/api/auth/login', json={'correo':'estudiante@monda.local','password':'Estudiante123!'})
        assert login.status_code == 200
        csrf = login.json()['csrfToken']
        denied = client.post('/api/auth/refresh')
        assert denied.status_code == 403
        refreshed = client.post('/api/auth/refresh', headers={'X-CSRF-Token': csrf})
        assert refreshed.status_code == 200, refreshed.text
        assert refreshed.json()['accessToken']


def test_rag_provider_modes_are_available_without_starting_servers():
    from backend.app.rag.providers.fallback import FallbackProvider
    from backend.app.rag.providers.ollama import OllamaProvider
    assert FallbackProvider().name == 'fallback'
    assert OllamaProvider().name == 'ollama'
