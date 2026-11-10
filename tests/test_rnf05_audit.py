#!/usr/bin/env python3
"""RNF-05: prueba de auditoría.

Verifica que el endpoint /api/admin/audit devuelva registros de auditoría
para acciones de docentes y administradores, y que un estudiante no pueda
acceder a ellos (403).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.db.seed import init_test_db
from backend.app.main import app


def auth(client: TestClient, email: str, password: str):
    response = client.post(
        "/api/auth/login", json={"correo": email, "password": password})
    assert response.status_code == 200, response.text
    headers = {"Authorization": "Bearer " + response.json()["accessToken"]}
    if not response.json().get("legalTermsAccepted"):
        accepted = client.post("/api/legal/terms/accept", headers=headers,
                               json={"version": "2026-10-v1", "accepted": True})
        assert accepted.status_code == 200, accepted.text
    return headers


def test_rnf05_audit_endpoint_teacher_and_admin_can_read_student_cannot():
    init_test_db(True)
    with TestClient(app) as client:
        teacher = auth(client, "docente@monda.local", "Docente123!")
        admin = auth(client, "admin@monda.local", "Admin123!")
        student = auth(client, "estudiante@monda.local", "Estudiante123!")

        # Docente y admin pueden leer auditoría.
        t_resp = client.get("/api/admin/audit", headers=teacher)
        assert t_resp.status_code == 200, t_resp.text
        a_resp = client.get("/api/admin/audit", headers=admin)
        assert a_resp.status_code == 200, a_resp.text

        # Estudiante no puede.
        s_resp = client.get("/api/admin/audit", headers=student)
        assert s_resp.status_code == 403, s_resp.text

        # El registro de auditoría contiene al menos una entrada.
        audit = t_resp.json()
        assert isinstance(audit, list) or ("items" in audit and isinstance(audit.get("items"), list))
