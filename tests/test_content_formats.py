from io import BytesIO

from docx import Document
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from backend.app.db.seed import init_test_db
from backend.app.main import app


def teacher_headers(client):
    response = client.post(
        "/api/auth/login",
        json={"correo": "docente@monda.local", "password": "Docente123!"},
    )
    assert response.status_code == 200
    headers = {"Authorization": "Bearer " + response.json()["accessToken"]}
    if not response.json().get("legalTermsAccepted"):
        accepted = client.post(
            "/api/legal/terms/accept",
            headers=headers,
            json={"version": "2026-10-v1", "accepted": True},
        )
        assert accepted.status_code == 200
    return headers


def upload(client, headers, filename, data, mime):
    course_id = client.get("/api/courses", headers=headers).json()["items"][0]["id"]
    response = client.post(
        f"/api/courses/{course_id}/contents",
        headers=headers,
        data={"acceptSharingTerms": "true", "sharingTermsVersion": "2026-10-v1"},
        files={"file": (filename, data, mime)},
    )
    assert response.status_code == 201, response.text
    return course_id, response.json()["contentId"]


def test_docx_upload_extracts_and_indexes_text():
    init_test_db(True)
    with TestClient(app) as client:
        headers = teacher_headers(client)
        document = Document()
        document.add_paragraph(
            "La reciprocidad andina describe el intercambio de ayuda entre comunidades."
        )
        buffer = BytesIO()
        document.save(buffer)
        course_id, content_id = upload(
            client,
            headers,
            "reciprocidad.docx",
            buffer.getvalue(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        indexed = client.post(f"/api/contents/{content_id}/index", headers=headers)
        assert indexed.status_code == 202
        job = client.get(f"/api/jobs/{indexed.json()['jobId']}", headers=headers).json()
        assert job["estado"] == "completado", job
        assert job["result"]["fragmentCount"] >= 1
        status = client.get(f"/api/contents/{content_id}/status", headers=headers).json()
        assert status == {"estado": "indexado", "errorCode": None, "fragmentCount": 1}

        response = client.post(
            f"/api/courses/{course_id}/rag/query",
            headers=headers,
            json={"question": "¿Qué describe la reciprocidad andina?", "contentIds": [content_id]},
        )
        assert response.status_code == 200, response.text
        assert response.json()["sources"][0]["contentId"] == content_id


def test_scanned_pdf_returns_specific_ocr_required_status():
    init_test_db(True)
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    buffer = BytesIO()
    writer.write(buffer)

    with TestClient(app) as client:
        headers = teacher_headers(client)
        _, content_id = upload(
            client, headers, "escaneado.pdf", buffer.getvalue(), "application/pdf"
        )
        indexed = client.post(f"/api/contents/{content_id}/index", headers=headers)
        job = client.get(f"/api/jobs/{indexed.json()['jobId']}", headers=headers).json()

        assert job["estado"] == "error"
        assert job["result"]["errorCode"] == "OCR_REQUIRED"
        status = client.get(f"/api/contents/{content_id}/status", headers=headers).json()
        assert status["estado"] == "error"
        assert status["errorCode"] == "OCR_REQUIRED"
        assert status["fragmentCount"] == 0
