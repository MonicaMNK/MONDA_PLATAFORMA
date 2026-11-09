import json
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.db.seed import DEMO_CATALOG_PATH, init_test_db
from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models import Audit, Content, Course, RAGFragment, User
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
    headers = {"Authorization": "Bearer " + response.json()["accessToken"]}
    if not response.json().get("legalTermsAccepted"):
        accepted = client.post("/api/legal/terms/accept", headers=headers,
                               json={"version": "2026-10-v1", "accepted": True})
        assert accepted.status_code == 200, accepted.text
    return headers, response


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


def test_demo_seed_has_three_courses_and_nine_pdf_records(demo):
    from backend.app.db.seed import seed_demo_data

    catalog = json.loads(DEMO_CATALOG_PATH.read_text(encoding="utf-8"))
    ocr_files = {
        material["filename"]
        for course in catalog["courses"]
        for material in course["materials"]
        if material.get("requires_ocr")
    }
    assert len(ocr_files) == 1
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
                if item.nombre_original in ocr_files:
                    assert not item.activo and item.estado_indexacion == "error"
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


def test_platform_terms_are_required_and_versioned(demo):
    response = demo.post(
        '/api/auth/login', json={'correo': 'estudiante@monda.local', 'password': 'Estudiante123!'})
    assert response.status_code == 200
    headers = {'Authorization': 'Bearer ' + response.json()['accessToken']}
    assert response.json()['legalTermsAccepted'] is False
    assert demo.get('/api/legal/terms/status',
                    headers=headers).json()['accepted'] is False
    assert demo.get('/api/courses', headers=headers).status_code == 428
    terms = demo.get('/api/legal/terms', headers=headers)
    assert terms.status_code == 200
    version = terms.json()['version']
    assert demo.post('/api/legal/terms/accept', headers=headers,
                     json={'version': version, 'accepted': False}).status_code == 422
    accepted = demo.post('/api/legal/terms/accept', headers=headers,
                         json={'version': version, 'accepted': True})
    assert accepted.status_code == 200
    assert demo.get('/api/legal/terms/status',
                    headers=headers).json()['accepted'] is True
    assert demo.get('/api/courses', headers=headers).status_code == 200
    with SessionLocal() as db:
        assert db.query(Audit).filter_by(
            accion='PLATFORM_TERMS_ACCEPT', objeto=f'version:{version}').count() == 1


def test_teacher_must_accept_material_sharing_terms_for_each_upload(demo, monkeypatch):
    headers, _ = login(demo, 'docente@monda.local', 'Docente123!')
    course_id = demo.get(
        '/api/courses', headers=headers).json()['items'][0]['id']
    base = f'/api/courses/{course_id}/contents'
    payload = {
        'file': ('material.pdf', b'%PDF-demo-content', 'application/pdf')}
    assert demo.post(base, headers=headers, files=payload).status_code == 422
    uploaded = demo.post(base, headers=headers, files=payload, data={
                         'acceptSharingTerms': 'true', 'sharingTermsVersion': '2026-10-v1'})
    assert uploaded.status_code == 201, uploaded.text

    from types import SimpleNamespace
    import backend.app.api.v1.routers.contents as contents_router
    from backend.app.services import content_service
    monkeypatch.setattr(contents_router, 'settings',
                        SimpleNamespace(max_upload_bytes=10))
    monkeypatch.setattr(content_service, 'settings',
                        SimpleNamespace(max_upload_bytes=10))
    terms = {'acceptSharingTerms': 'true', 'sharingTermsVersion': '2026-10-v1'}
    unsupported = demo.post(
        base, headers=headers,
        files={'file': ('not-supported.txt', b'plain text', 'text/plain')}, data=terms,
    )
    assert unsupported.status_code == 415
    oversized = demo.post(
        base, headers=headers,
        files={'file': ('too-large.pdf', b'12345678901', 'application/pdf')}, data=terms,
    )
    assert oversized.status_code == 413
    with SessionLocal() as db:
        record = db.query(Audit).filter_by(
            accion='CONTENT_SHARING_ACCEPT',
            objeto=f"course:{course_id};content:{uploaded.json()['contentId']};version:2026-10-v1",
        ).one()
        assert record.actor_id is not None


@pytest.mark.parametrize(
    ("question", "query_vector", "evidence_expected"),
    [
        ("¿Qué explica el material sobre reciprocidad?",
         [1.0] + [0.0] * 767, True),
        ("¿Qué dosis recomienda para una enfermedad ajena al material?",
         [0.0, 1.0] + [0.0] * 766, False),
    ],
)
def test_gemini_mode_rag_api_with_controlled_provider_generates_cited_answer_or_abstains(
    demo, monkeypatch, question, query_vector, evidence_expected
):
    from backend.app.models import Config
    from backend.app.rag.providers.base import GenerationResult
    from backend.app.services import rag_service

    class ControlledGeminiProvider:
        name = "gemini"
        embedding_model = "gemini-integration-test-768"
        llm_model = "gemini-integration-test"
        supports_embeddings = True
        supports_generation = True
        last_generation_model = llm_model
        last_generation_warning = None

        def __init__(self):
            self.generation_calls = 0
            self.embedding_tasks = []

        def embed(self, texts, task="document"):
            self.embedding_tasks.append(task)
            assert len(texts) == 1
            return [query_vector]

        def generate(self, prompt):
            self.generation_calls += 1
            assert "[F1 | fragmentId=" in prompt
            assert "El Tahuantinsuyo.pdf" not in prompt
            return GenerationResult("La fuente describe la reciprocidad andina [F1].")

    provider = ControlledGeminiProvider()
    monkeypatch.setattr(
        rag_service, "get_provider_with_fallback", lambda *args, **kwargs: (
            provider, None)
    )
    monkeypatch.setattr(rag_service, "trace_rag",
                        lambda *_args, **_kwargs: None)

    with SessionLocal() as db:
        course = db.query(Course).filter_by(nombre="Historia").one()
        content = db.query(Content).filter_by(
            curso_id=course.id, nombre_original="El Tahuantinsuyo.pdf"
        ).one()
        fragment = db.query(RAGFragment).filter_by(
            contenido_id=content.id).first()
        fragment.embedding = [1.0] + [0.0] * 767
        fragment.embedding_model = provider.embedding_model
        fragment.embedding_provider = provider.name
        rag_config = db.get(Config, "rag")
        rag_config.valor = {**rag_config.valor,
                            "mode": "gemini", "topK": 1, "umbral": 0.62}
        course_id = course.id
        db.commit()

    headers, _ = login(demo, "docente@monda.local", "Docente123!")
    response = demo.post(
        f"/api/courses/{course_id}/rag/query",
        headers=headers,
        json={"question": question},
    )

    assert response.status_code == 200, response.text
    result = response.json()
    assert provider.embedding_tasks == ["query"]
    assert result["mode"] == "gemini"
    assert result["evidenceSufficient"] is evidence_expected
    if evidence_expected:
        assert provider.generation_calls == 1
        assert "[F1]" in result["answer"]
        assert result["sources"][0]["nombre"] == "El Tahuantinsuyo.pdf"
    else:
        assert provider.generation_calls == 0
        assert "No encuentro evidencia suficiente" in result["answer"]
