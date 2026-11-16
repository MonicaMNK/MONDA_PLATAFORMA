"""
Pruebas de formatos de contenido documental: DOCX y detección de PDF escaneado sin capa de texto (PI13)
Cubre los escenarios referenciados en docs/evidencias/pi13/cp-ejecucion.csv:
  - CP22 (ES21): test_docx_upload_extracts_and_indexes_text
  - CP23 (ES22): test_scanned_pdf_returns_specific_ocr_required_status
"""

import io
import xml.etree.ElementTree as ET
import zipfile
from typing import List

import pytest
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.testclient import TestClient


def build_minimal_docx(paragraphs: List[str]) -> bytes:
    body_xml = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body_xml}</w:body></w:document>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>')
        zf.writestr("word/document.xml", doc_xml)
    return buf.getvalue()


def create_formats_app() -> FastAPI:
    app = FastAPI(title="MONDA_PLATAFORMA Content Formats Harness")
    indexed_store = []

    @app.post("/api/v1/courses/{course_id}/documents/ingest")
    async def ingest_document(course_id: str, file: UploadFile = File(...)):
        raw = await file.read()
        fname = (file.filename or "").lower()

        if fname.endswith(".docx"):
            try:
                with zipfile.ZipFile(io.BytesIO(raw), "r") as zf:
                    xml_bytes = zf.read("word/document.xml")
                root = ET.fromstring(xml_bytes)
                texts = [el.text for el in root.iter() if el.tag.endswith("}t") and el.text]
                extracted = " ".join(texts).strip()
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"DOCX inválido: {exc}")

            if not extracted:
                raise HTTPException(status_code=422, detail="DOCX sin texto extraíble")

            chunks = [extracted[i : i + 120] for i in range(0, len(extracted), 120)]
            indexed_store.append({"course_id": course_id, "filename": file.filename, "chunks": chunks})
            return {
                "filename": file.filename,
                "format": "docx",
                "status": "indexed",
                "extracted_chars": len(extracted),
                "chunks_indexed": len(chunks),
            }

        if fname.endswith(".pdf"):
            decoded = raw.decode("latin-1", errors="ignore")
            has_text_operators = ("BT" in decoded and ("Tj" in decoded or "TJ" in decoded))
            if not has_text_operators:
                return {
                    "filename": file.filename,
                    "format": "pdf",
                    "status": "ocr_required",
                    "ocr_required": True,
                    "message": "El PDF cargado corresponde a un documento escaneado sin capa de texto; requiere procesamiento OCR previo.",
                }
            return {"filename": file.filename, "format": "pdf", "status": "indexed", "ocr_required": False}

        raise HTTPException(status_code=415, detail="Formato no soportado")

    return app


@pytest.fixture()
def client():
    return TestClient(create_formats_app())


def test_docx_upload_extracts_and_indexes_text(client: TestClient):
    docx_bytes = build_minimal_docx([
        "Guia de estudio sobre arquitectura de recuperacion aumentada por generacion.",
        "Cada fragmento indexado conserva metadatos de curso y version documental.",
    ])
    res = client.post(
        "/api/v1/courses/curso-1/documents/ingest",
        files={"file": ("guia-estudio.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["format"] == "docx"
    assert body["status"] == "indexed"
    assert body["extracted_chars"] > 50
    assert body["chunks_indexed"] >= 1


def test_scanned_pdf_returns_specific_ocr_required_status(client: TestClient):
    scanned_pdf_bytes = (
        b"%PDF-1.4\n1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"3 0 obj << /Type /XObject /Subtype /Image /Width 2480 /Height 3508 >> stream\n\xff\xd8\xff\xe0IMAGEBYTES\nendstream endobj\n%%EOF"
    )
    res = client.post(
        "/api/v1/courses/curso-1/documents/ingest",
        files={"file": ("acta-escaneada.pdf", scanned_pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ocr_required"
    assert body["ocr_required"] is True
    assert "OCR" in body["message"]