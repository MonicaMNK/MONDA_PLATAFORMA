from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.db.seed import init_test_db
from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models import Content, Course, RAGFragment, User
from backend.app.rag.retrieval import vector_search
from backend.app.services.content_service import create_content
from backend.app.services.assessment_service import generate_assessment


@pytest.fixture
def demo():
    init_test_db(True)
    with TestClient(app) as client:
        yield client


def login(client, email="estudiante@monda.local", password="Estudiante123!"):
    response = client.post(
        "/api/auth/login", json={"correo": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["accessToken"]}, response


def test_csrf_cookie_visible_at_home_and_logout_clears_it(demo):
    _, response = login(demo)
    cookie = next(c for c in demo.cookies.jar if c.name == "monda_csrf")
    assert cookie.path == "/"
    csrf = response.json()["csrfToken"]
    assert demo.post("/api/auth/refresh",
                     headers={"X-CSRF-Token": csrf}).status_code == 200
    assert demo.post("/api/auth/logout",
                     headers={"X-CSRF-Token": csrf}).status_code == 204
    assert not any(c.name == "monda_csrf" for c in demo.cookies.jar)


def test_sync_checks_course_and_full_action_identity(demo):
    headers, _ = login(demo)
    with SessionLocal() as db:
        teacher = db.query(User).filter_by(rol="docente").first()
        course = Course(docente_id=teacher.id,
                        nombre="Curso ajeno", estado="activo")
        db.add(course)
        db.commit()
        course_id = course.id
    action = {"actionId": str(uuid4()), "tipo": "borrador_personal",
              "version": 1, "payload": {"courseId": course_id}}
    result = demo.post("/api/sync", headers=headers,
                       json={"actions": [action]})
    assert result.json()["results"][0]["status"] == "rejected"
    action["actionId"] = str(uuid4())
    action["payload"] = {"text": "nota"}
    assert demo.post("/api/sync", headers=headers,
                     json={"actions": [action]}).json()["results"][0]["status"] == "applied"
    action["version"] = 2
    assert demo.post("/api/sync", headers=headers,
                     json={"actions": [action]}).json()["results"][0]["status"] == "conflict"


def test_document_cannot_be_reused_in_another_course(demo):
    with SessionLocal() as db:
        teacher = db.query(User).filter_by(rol="docente").first()
        content = db.query(Content).filter_by(
            nombre_original="El Imperio Inca.pdf").first()
        course = Course(docente_id=teacher.id,
                        nombre="Otro curso", estado="activo")
        db.add(course)
        db.commit()
        with pytest.raises(HTTPException) as exc:
            create_content(db, teacher, course.id, "material.pdf",
                           "application/pdf", b"data", content.documento_id, 2)
        assert exc.value.status_code == 403
        assert db.get(Content, content.id).activo


def test_vector_search_excludes_other_embedding_spaces(demo):
    with SessionLocal() as db:
        fragment = db.query(RAGFragment).first()
        fragment.embedding = [1.0] + [0.0] * 767
        fragment.embedding_model = "model-a"
        fragment.embedding_provider = "provider-a"
        db.commit()
        vector = [1.0] + [0.0] * 767
        assert len(vector_search(db, fragment.curso_id,
                   vector, 4, "model-a", "provider-a")) == 1
        assert vector_search(db, fragment.curso_id, vector,
                             4, "model-b", "provider-a") == []
        assert vector_search(db, fragment.curso_id, vector,
                             4, "model-a", "provider-b") == []


def test_assessment_does_not_use_inactive_material(demo):
    with SessionLocal() as db:
        teacher = db.query(User).filter_by(rol="docente").first()
        course = db.query(Course).first()
        for content in db.query(Content).filter_by(curso_id=course.id).all():
            content.activo = False
        db.commit()
        with pytest.raises(HTTPException) as exc:
            generate_assessment(db, teacher, course.id, "tema inexistente",
                                "comprender", "media", 2, "opcion_multiple")
        assert exc.value.status_code == 422


def test_reindex_active_material_keeps_it_available(demo, monkeypatch):
    from backend.app.services import content_service
    from backend.app.rag.providers.fallback import FallbackProvider
    monkeypatch.setattr(content_service, 'get_provider_with_fallback',
                        lambda *a, **kw: (FallbackProvider(), None))
    with SessionLocal() as db:
        teacher = db.query(User).filter_by(rol='docente').first()
        content = db.query(Content).filter_by(
            nombre_original='El Imperio Inca.pdf').first()
        content.modelo_embedding = 'old-model'
        db.commit()
        job = content_service.index_content(db, teacher, content)
        assert job.estado == 'completado'
        db.expire_all()
        assert db.get(Content, content.id).activo
        assert db.get(
            Content, content.id).modelo_embedding == 'fallback-lexical-v1'


def test_demo_seed_has_three_courses_and_nine_visible_pdfs(demo):
    from backend.app.db.seed import seed_demo_data

    with SessionLocal() as db:
        courses = db.query(Course).all()
        assert len(courses) == 3
        content_ids = set()
        for course in courses:
            contents = db.query(Content).filter_by(curso_id=course.id).all()
            assert len(contents) == 3
            assert all(item.mime_type ==
                       "application/pdf" for item in contents)
            for item in contents:
                fragment_count = db.query(RAGFragment).filter_by(
                    contenido_id=item.id).count()
                if item.nombre_original == "El Descubrimiento de Amèrica.pdf":
                    assert item.estado_indexacion == "error" and not item.activo
                    assert fragment_count == 0
                else:
                    assert item.activo and item.estado_indexacion == "indexado"
                    assert fragment_count > 0
            content_ids.update(item.id for item in contents)

    seed_demo_data()

    with SessionLocal() as db:
        assert db.query(Course).count() == 3
        assert db.query(Content).count() == 9
        assert {item.id for item in db.query(Content).all()} == content_ids
