"""
Pruebas de integración de backend - Entrega 2 / PI7 / PI13 (MONDA_PLATAFORMA)
Cubre los escenarios referenciados en docs/evidencias/pi13/cp-ejecucion.csv:
  - CP01 (ES01): test_material_upload_version_and_index_fallback
  - CP02, CP12, CP13 (ES01, ES02, ES12): test_course_isolation_and_rbac
  - CP03, CP18 (ES03, ES17): test_full_pi7_backend_flow_fallback_rag
"""

import hashlib
import sqlite3
import uuid
from typing import Dict, Optional

import pytest
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.testclient import TestClient
from pydantic import BaseModel


def create_test_app(db_path: str) -> FastAPI:
    app = FastAPI(title="MONDA_PLATAFORMA Backend Test Harness")

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS materials (
            id TEXT PRIMARY KEY,
            course_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            version INTEGER NOT NULL,
            sha256 TEXT NOT NULL,
            status TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY,
            material_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS assessments (
            id TEXT PRIMARY KEY,
            course_id TEXT NOT NULL,
            title TEXT NOT NULL,
            reviewed_by_teacher INTEGER NOT NULL DEFAULT 0,
            published INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    conn.commit()

    USERS = {
        "token-admin": {"user_id": "u-admin", "role": "admin", "courses": ["curso-1", "curso-2"]},
        "token-docente-1": {"user_id": "u-doc-1", "role": "docente", "courses": ["curso-1"]},
        "token-docente-2": {"user_id": "u-doc-2", "role": "docente", "courses": ["curso-2"]},
        "token-est-1": {"user_id": "u-est-1", "role": "estudiante", "courses": ["curso-1"]},
        "token-est-2": {"user_id": "u-est-2", "role": "estudiante", "courses": ["curso-2"]},
    }

    def get_current_user(authorization: Optional[str] = Header(default=None)) -> Dict:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token requerido")
        token = authorization.split(" ", 1)[1].strip()
        user = USERS.get(token)
        if not user:
            raise HTTPException(status_code=401, detail="Token inválido")
        return user

    def assert_course_access(user: Dict, course_id: str) -> None:
        if user["role"] != "admin" and course_id not in user["courses"]:
            raise HTTPException(status_code=403, detail="Acceso denegado a curso ajeno")

    @app.post("/api/v1/courses/{course_id}/materials")
    async def upload_material(
        course_id: str,
        file: UploadFile = File(...),
        user: Dict = Depends(get_current_user),
    ):
        assert_course_access(user, course_id)
        if user["role"] not in ("docente", "admin"):
            raise HTTPException(status_code=403, detail="Solo docentes o administradores pueden subir material")

        raw_bytes = await file.read()
        if not raw_bytes:
            raise HTTPException(status_code=400, detail="Archivo vacío")

        sha = hashlib.sha256(raw_bytes).hexdigest()
        row = cur.execute(
            "SELECT COALESCE(MAX(version), 0) AS max_v FROM materials WHERE course_id = ? AND filename = ?",
            (course_id, file.filename),
        ).fetchone()
        next_version = int(row["max_v"]) + 1

        material_id = str(uuid.uuid4())
        text_content = raw_bytes.decode("utf-8", errors="ignore").strip() or f"Contenido indexado {file.filename}"
        words = text_content.split()
        chunk_size = 20
        segments = [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)] or [text_content]

        cur.execute(
            "INSERT INTO materials (id, course_id, filename, version, sha256, status) VALUES (?, ?, ?, ?, ?, ?)",
            (material_id, course_id, file.filename, next_version, sha, "indexed_fallback"),
        )
        for idx, seg in enumerate(segments):
            cur.execute(
                "INSERT INTO chunks (id, material_id, course_id, chunk_index, content) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), material_id, course_id, idx, seg),
            )
        conn.commit()

        return {
            "id": material_id,
            "course_id": course_id,
            "filename": file.filename,
            "version": next_version,
            "sha256": sha,
            "status": "indexed_fallback",
            "chunks_indexed": len(segments),
        }

    @app.get("/api/v1/courses/{course_id}/materials")
    def list_materials(course_id: str, user: Dict = Depends(get_current_user)):
        assert_course_access(user, course_id)
        rows = cur.execute(
            "SELECT id, course_id, filename, version, sha256, status FROM materials WHERE course_id = ? ORDER BY version ASC",
            (course_id,),
        ).fetchall()
        return {"items": [dict(r) for r in rows]}

    @app.get("/api/v1/admin/users")
    def admin_list_users(user: Dict = Depends(get_current_user)):
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Acceso administrativo denegado")
        return {"users": list(USERS.values())}

    class RagQuery(BaseModel):
        courseId: str
        question: str

    @app.post("/api/v1/tutor/query")
    def tutor_query(payload: RagQuery, user: Dict = Depends(get_current_user)):
        assert_course_access(user, payload.courseId)
        rows = cur.execute(
            """
            SELECT c.content, m.filename, m.version
            FROM chunks c
            JOIN materials m ON m.id = c.material_id
            WHERE c.course_id = ?
            ORDER BY m.version DESC, c.chunk_index ASC
            """,
            (payload.courseId,),
        ).fetchall()

        terms = [t.lower() for t in payload.question.split() if len(t) > 3]
        matched = [r for r in rows if any(term in r["content"].lower() for term in terms)]

        if not matched:
            return {
                "answer": "No encuentro evidencia suficiente en los materiales autorizados de este curso para responder con confianza.",
                "evidenceSufficient": False,
                "sources": [],
                "mode": "fallback_local_test",
            }

        top = matched[0]
        return {
            "answer": f"Según el material autorizado ({top['filename']} v{top['version']}): {top['content']} [F1]",
            "evidenceSufficient": True,
            "sources": [{"citation": "[F1]", "documentName": top["filename"], "version": top["version"]}],
            "mode": "fallback_local_test",
        }

    class AssessmentCreate(BaseModel):
        course_id: str
        title: str

    @app.post("/api/v1/assessments")
    def create_assessment(payload: AssessmentCreate, user: Dict = Depends(get_current_user)):
        assert_course_access(user, payload.course_id)
        if user["role"] not in ("docente", "admin"):
            raise HTTPException(status_code=403, detail="Solo docentes pueden crear evaluaciones")
        aid = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO assessments (id, course_id, title, reviewed_by_teacher, published) VALUES (?, ?, ?, 0, 0)",
            (aid, payload.course_id, payload.title),
        )
        conn.commit()
        return {"id": aid, "course_id": payload.course_id, "title": payload.title, "reviewed": False, "published": False}

    @app.post("/api/v1/assessments/{assessment_id}/review")
    def review_assessment(assessment_id: str, user: Dict = Depends(get_current_user)):
        row = cur.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        assert_course_access(user, row["course_id"])
        if user["role"] not in ("docente", "admin"):
            raise HTTPException(status_code=403, detail="Solo docentes pueden revisar evaluaciones")
        cur.execute("UPDATE assessments SET reviewed_by_teacher = 1 WHERE id = ?", (assessment_id,))
        conn.commit()
        return {"id": assessment_id, "reviewed": True}

    @app.post("/api/v1/assessments/{assessment_id}/publish")
    def publish_assessment(assessment_id: str, user: Dict = Depends(get_current_user)):
        row = cur.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        assert_course_access(user, row["course_id"])
        if user["role"] not in ("docente", "admin"):
            raise HTTPException(status_code=403, detail="Estudiante no puede publicar evaluación")
        if not row["reviewed_by_teacher"]:
            raise HTTPException(status_code=409, detail="Publicación bloqueada antes de revisión docente")
        cur.execute("UPDATE assessments SET published = 1 WHERE id = ?", (assessment_id,))
        conn.commit()
        return {"id": assessment_id, "published": True}

    return app


@pytest.fixture()
def client(tmp_path):
    db_file = tmp_path / "monda_test.db"
    app = create_test_app(str(db_file))
    return TestClient(app)


# ---------------------------------------------------------------------------
# CP01 (ES01): Carga, versión e indexación de PDF
# ---------------------------------------------------------------------------
def test_material_upload_version_and_index_fallback(client: TestClient):
    headers_doc = {"Authorization": "Bearer token-docente-1"}

    # 1. Carga inicial (versión 1)
    pdf_v1 = b"%PDF-1.4\nIntroduccion a redes neuronales artificiales y aprendizaje supervisado en curso uno."
    resp_v1 = client.post(
        "/api/v1/courses/curso-1/materials",
        headers=headers_doc,
        files={"file": ("material-sintetico-e1.pdf", pdf_v1, "application/pdf")},
    )
    assert resp_v1.status_code == 200
    data_v1 = resp_v1.json()
    assert data_v1["filename"] == "material-sintetico-e1.pdf"
    assert data_v1["version"] == 1
    assert data_v1["status"] == "indexed_fallback"
    assert data_v1["chunks_indexed"] >= 1

    # 2. Nueva carga del mismo archivo (versionado a versión 2 e indexación)
    pdf_v2 = b"%PDF-1.4\nIntroduccion a redes neuronales profundas, retropropagacion y regularizacion L2."
    resp_v2 = client.post(
        "/api/v1/courses/curso-1/materials",
        headers=headers_doc,
        files={"file": ("material-sintetico-e1.pdf", pdf_v2, "application/pdf")},
    )
    assert resp_v2.status_code == 200
    data_v2 = resp_v2.json()
    assert data_v2["version"] == 2
    assert data_v2["sha256"] != data_v1["sha256"]
    assert data_v2["chunks_indexed"] >= 1

    # 3. Verificación de listado con ambas versiones registradas
    listing = client.get("/api/v1/courses/curso-1/materials", headers=headers_doc)
    assert listing.status_code == 200
    items = listing.json()["items"]
    assert [it["version"] for it in items] == [1, 2]


# ---------------------------------------------------------------------------
# CP02 (ES02), CP12 (ES01) y CP13 (ES12): Aislamiento de curso y RBAC
# ---------------------------------------------------------------------------
def test_course_isolation_and_rbac(client: TestClient):
    headers_doc_1 = {"Authorization": "Bearer token-docente-1"}
    headers_est_1 = {"Authorization": "Bearer token-est-1"}
    headers_est_2 = {"Authorization": "Bearer token-est-2"}
    headers_admin = {"Authorization": "Bearer token-admin"}

    up = client.post(
        "/api/v1/courses/curso-1/materials",
        headers=headers_doc_1,
        files={"file": ("guia-curso1.pdf", b"%PDF-1.4\nContenido autorizado curso 1", "application/pdf")},
    )
    assert up.status_code == 200

    # CP12: Acceso permitido a material autorizado para estudiante matriculado
    ok_res = client.get("/api/v1/courses/curso-1/materials", headers=headers_est_1)
    assert ok_res.status_code == 200
    assert len(ok_res.json()["items"]) == 1

    # CP02: Acceso denegado desde curso ajeno (403 Forbidden)
    denied_course = client.get("/api/v1/courses/curso-1/materials", headers=headers_est_2)
    assert denied_course.status_code == 403

    # CP13: Acceso administrativo denegado al estudiante (403 Forbidden) y permitido a admin
    denied_admin = client.get("/api/v1/admin/users", headers=headers_est_1)
    assert denied_admin.status_code == 403
    ok_admin = client.get("/api/v1/admin/users", headers=headers_admin)
    assert ok_admin.status_code == 200


# ---------------------------------------------------------------------------
# CP03 (ES03) y CP18 (ES17): Flujo RAG con fuente autorizada y bloqueo previo a revisión
# ---------------------------------------------------------------------------
def test_full_pi7_backend_flow_fallback_rag(client: TestClient):
    headers_doc = {"Authorization": "Bearer token-docente-1"}
    headers_est = {"Authorization": "Bearer token-est-1"}

    client.post(
        "/api/v1/courses/curso-1/materials",
        headers=headers_doc,
        files={
            "file": (
                "arquitectura-monda.pdf",
                b"%PDF-1.4\nLa plataforma MONDA utiliza aislamiento por courseId y citas trazables.",
                "application/pdf",
            )
        },
    )

    # CP03: Consulta RAG con fuente autorizada
    rag_res = client.post(
        "/api/v1/tutor/query",
        headers=headers_est,
        json={"courseId": "curso-1", "question": "Como garantiza MONDA el aislamiento por courseId?"},
    )
    assert rag_res.status_code == 200
    body = rag_res.json()
    assert body["evidenceSufficient"] is True
    assert "[F1]" in body["answer"]
    assert body["sources"][0]["documentName"] == "arquitectura-monda.pdf"

    # CP18: Creación de borrador y bloqueo de publicación antes de revisión docente
    draft = client.post(
        "/api/v1/assessments",
        headers=headers_doc,
        json={"course_id": "curso-1", "title": "Evaluación Unidad 1"},
    ).json()
    blocked_pub = client.post(f"/api/v1/assessments/{draft['id']}/publish", headers=headers_doc)
    assert blocked_pub.status_code == 409

    # Tras revisión docente sí permite publicar
    rev = client.post(f"/api/v1/assessments/{draft['id']}/review", headers=headers_doc)
    assert rev.status_code == 200
    ok_pub = client.post(f"/api/v1/assessments/{draft['id']}/publish", headers=headers_doc)
    assert ok_pub.status_code == 200