"""
Pruebas de gestión administrativa, asignación de cursos y bloqueo de exportación a docente ajeno (PI13)
Cubre el escenario referenciado en docs/evidencias/pi13/cp-ejecucion.csv:
  - CP21 (ES20): test_admin_creates_edits_users_and_assigns_courses
"""

import sqlite3
from typing import Dict, Optional

import pytest
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel


def create_admin_app(db_path: str) -> FastAPI:
    app = FastAPI(title="MONDA_PLATAFORMA Admin & Export Harness")

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS course_assignments (
            user_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            PRIMARY KEY (user_id, course_id)
        );
        """
    )
    cur.execute("INSERT INTO users (id, email, role, active) VALUES ('u-admin', 'admin@monda.edu', 'admin', 1)")
    conn.commit()

    def get_current_user(authorization: Optional[str] = Header(default=None)) -> Dict:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token requerido")
        uid = authorization.split(" ", 1)[1].strip()
        row = cur.execute("SELECT * FROM users WHERE id = ? AND active = 1", (uid,)).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Usuario no válido o inactivo")
        courses = [
            r["course_id"]
            for r in cur.execute("SELECT course_id FROM course_assignments WHERE user_id = ?", (uid,)).fetchall()
        ]
        return {"id": row["id"], "email": row["email"], "role": row["role"], "courses": courses}

    class UserCreate(BaseModel):
        id: str
        email: str
        role: str

    class UserUpdate(BaseModel):
        role: Optional[str] = None
        active: Optional[bool] = None

    class CourseAssign(BaseModel):
        course_id: str

    @app.post("/api/v1/admin/users")
    def create_user(payload: UserCreate, user: Dict = Depends(get_current_user)):
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Solo administradores")
        cur.execute(
            "INSERT INTO users (id, email, role, active) VALUES (?, ?, ?, 1)",
            (payload.id, payload.email, payload.role),
        )
        conn.commit()
        return {"id": payload.id, "email": payload.email, "role": payload.role, "active": True}

    @app.patch("/api/v1/admin/users/{target_id}")
    def edit_user(target_id: str, payload: UserUpdate, user: Dict = Depends(get_current_user)):
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Solo administradores")
        if payload.role is not None:
            cur.execute("UPDATE users SET role = ? WHERE id = ?", (payload.role, target_id))
        if payload.active is not None:
            cur.execute("UPDATE users SET active = ? WHERE id = ?", (1 if payload.active else 0, target_id))
        conn.commit()
        row = cur.execute("SELECT * FROM users WHERE id = ?", (target_id,)).fetchone()
        return dict(row)

    @app.post("/api/v1/admin/users/{target_id}/courses")
    def assign_course(target_id: str, payload: CourseAssign, user: Dict = Depends(get_current_user)):
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Solo administradores")
        cur.execute(
            "INSERT OR IGNORE INTO course_assignments (user_id, course_id) VALUES (?, ?)",
            (target_id, payload.course_id),
        )
        conn.commit()
        return {"user_id": target_id, "course_id": payload.course_id, "assigned": True}

    @app.get("/api/v1/courses/{course_id}/grades/export")
    def export_course_grades(course_id: str, user: Dict = Depends(get_current_user)):
        if user["role"] not in ("docente", "admin"):
            raise HTTPException(status_code=403, detail="Solo docentes asignados o administradores")
        if user["role"] != "admin" and course_id not in user["courses"]:
            raise HTTPException(status_code=403, detail="Exportación denegada a docente ajeno al curso")
        return {"course_id": course_id, "format": "csv", "rows": [{"student": "est-01", "grade_20": 15.5}]}

    return app


@pytest.fixture()
def client(tmp_path):
    return TestClient(create_admin_app(str(tmp_path / "admin_test.db")))


def test_admin_creates_edits_users_and_assigns_courses(client: TestClient):
    h_admin = {"Authorization": "Bearer u-admin"}

    r1 = client.post("/api/v1/admin/users", headers=h_admin, json={"id": "u-doc-a", "email": "doca@monda.edu", "role": "estudiante"})
    assert r1.status_code == 200
    r1_edit = client.patch("/api/v1/admin/users/u-doc-a", headers=h_admin, json={"role": "docente"})
    assert r1_edit.status_code == 200
    assert r1_edit.json()["role"] == "docente"

    r2 = client.post("/api/v1/admin/users", headers=h_admin, json={"id": "u-doc-b", "email": "docb@monda.edu", "role": "docente"})
    assert r2.status_code == 200

    assert client.post("/api/v1/admin/users/u-doc-a/courses", headers=h_admin, json={"course_id": "curso-1"}).status_code == 200
    assert client.post("/api/v1/admin/users/u-doc-b/courses", headers=h_admin, json={"course_id": "curso-2"}).status_code == 200

    ok_export = client.get("/api/v1/courses/curso-1/grades/export", headers={"Authorization": "Bearer u-doc-a"})
    assert ok_export.status_code == 200

    denied_export = client.get("/api/v1/courses/curso-1/grades/export", headers={"Authorization": "Bearer u-doc-b"})
    assert denied_export.status_code == 403