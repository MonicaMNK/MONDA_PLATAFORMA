"""
Pruebas de flujo de aprendizaje, calificación vigesimal (0-20) y alertas tempranas (PI11 / PI13)
Cubre los escenarios referenciados en docs/evidencias/pi13/cp-ejecucion.csv:
  - CP05 (ES05): test_es05_uno_de_tres_reactivos_califica_6_67_y_sin_intentos_cerrados_no_alerta
  - CP14 (ES13): test_cp_oe3_average_10_and_14_is_12_and_does_not_trigger_low_alert
  - CP19, CP20 (ES18, ES19): test_low_average_alert_requires_closed_attempts_and_uses_configured_threshold
"""

import sqlite3
import uuid

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel


def create_learning_app(db_path: str, alert_threshold: float = 11.0) -> FastAPI:
    app = FastAPI(title="MONDA_PLATAFORMA Learning Workflow Harness")
    app.state.alert_threshold = alert_threshold

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS attempts (
            id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            assessment_id TEXT NOT NULL,
            total_items INTEGER NOT NULL,
            correct_items INTEGER NOT NULL,
            score_20 REAL,
            status TEXT NOT NULL
        );
        """
    )
    conn.commit()

    class AttemptSubmit(BaseModel):
        student_id: str
        course_id: str
        assessment_id: str
        total_items: int
        correct_items: int
        status: str = "closed"  # "in_progress" | "closed"

    @app.post("/api/v1/attempts")
    def submit_attempt(payload: AttemptSubmit):
        if payload.total_items <= 0 or payload.correct_items < 0 or payload.correct_items > payload.total_items:
            raise HTTPException(status_code=400, detail="Conteo de reactivos inválido")

        score_20 = round((payload.correct_items / payload.total_items) * 20.0, 2) if payload.status == "closed" else None
        aid = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO attempts (id, student_id, course_id, assessment_id, total_items, correct_items, score_20, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                aid,
                payload.student_id,
                payload.course_id,
                payload.assessment_id,
                payload.total_items,
                payload.correct_items,
                score_20,
                payload.status,
            ),
        )
        conn.commit()
        return {
            "id": aid,
            "student_id": payload.student_id,
            "status": payload.status,
            "score_20": score_20,
        }

    @app.get("/api/v1/courses/{course_id}/students/{student_id}/summary")
    def get_student_summary(course_id: str, student_id: str):
        rows = cur.execute(
            "SELECT score_20 FROM attempts WHERE course_id = ? AND student_id = ? AND status = 'closed'",
            (course_id, student_id),
        ).fetchall()

        closed_scores = [float(r["score_20"]) for r in rows if r["score_20"] is not None]
        if not closed_scores:
            return {
                "student_id": student_id,
                "closed_attempts": 0,
                "average_20": None,
                "threshold": app.state.alert_threshold,
                "low_performance_alert": False,
            }

        avg = round(sum(closed_scores) / len(closed_scores), 2)
        return {
            "student_id": student_id,
            "closed_attempts": len(closed_scores),
            "average_20": avg,
            "threshold": app.state.alert_threshold,
            "low_performance_alert": avg < app.state.alert_threshold,
        }

    return app


@pytest.fixture()
def client(tmp_path):
    app = create_learning_app(str(tmp_path / "learning_test.db"), alert_threshold=11.0)
    return TestClient(app)


# ---------------------------------------------------------------------------
# CP05 (ES05): Evaluación y nota sobre veinte (1/3 -> 6.67)
# ---------------------------------------------------------------------------
def test_es05_uno_de_tres_reactivos_califica_6_67_y_sin_intentos_cerrados_no_alerta(client: TestClient):
    initial_summary = client.get("/api/v1/courses/curso-1/students/est-01/summary").json()
    assert initial_summary["closed_attempts"] == 0
    assert initial_summary["average_20"] is None
    assert initial_summary["low_performance_alert"] is False

    res = client.post(
        "/api/v1/attempts",
        json={
            "student_id": "est-01",
            "course_id": "curso-1",
            "assessment_id": "eval-01",
            "total_items": 3,
            "correct_items": 1,
            "status": "closed",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "closed"
    assert body["score_20"] == 6.67


# ---------------------------------------------------------------------------
# CP14 (ES13): Promedio de dos notas (10 y 14 -> 12.00) sin alerta
# ---------------------------------------------------------------------------
def test_cp_oe3_average_10_and_14_is_12_and_does_not_trigger_low_alert(client: TestClient):
    client.post(
        "/api/v1/attempts",
        json={"student_id": "est-02", "course_id": "curso-1", "assessment_id": "ev-1", "total_items": 20, "correct_items": 10, "status": "closed"},
    )
    client.post(
        "/api/v1/attempts",
        json={"student_id": "est-02", "course_id": "curso-1", "assessment_id": "ev-2", "total_items": 20, "correct_items": 14, "status": "closed"},
    )
    summary = client.get("/api/v1/courses/curso-1/students/est-02/summary").json()
    assert summary["closed_attempts"] == 2
    assert summary["average_20"] == 12.0
    assert summary["low_performance_alert"] is False


# ---------------------------------------------------------------------------
# CP19 (ES18) y CP20 (ES19): Reglas de alerta temprana según umbral
# ---------------------------------------------------------------------------
def test_low_average_alert_requires_closed_attempts_and_uses_configured_threshold(client: TestClient):
    # CP19: Intento en progreso (no cerrado) no dispara alerta
    client.post(
        "/api/v1/attempts",
        json={"student_id": "est-03", "course_id": "curso-1", "assessment_id": "ev-1", "total_items": 10, "correct_items": 2, "status": "in_progress"},
    )
    s_open = client.get("/api/v1/courses/curso-1/students/est-03/summary").json()
    assert s_open["closed_attempts"] == 0
    assert s_open["low_performance_alert"] is False

    # CP20: Intento cerrado con nota 8.00 (< umbral 11.00) sí dispara alerta
    client.post(
        "/api/v1/attempts",
        json={"student_id": "est-03", "course_id": "curso-1", "assessment_id": "ev-1", "total_items": 10, "correct_items": 4, "status": "closed"},
    )
    s_closed = client.get("/api/v1/courses/curso-1/students/est-03/summary").json()
    assert s_closed["closed_attempts"] == 1
    assert s_closed["average_20"] == 8.0
    assert s_closed["low_performance_alert"] is True