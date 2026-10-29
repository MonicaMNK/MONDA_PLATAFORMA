from __future__ import annotations

import hashlib
import json
import uuid

from sqlalchemy import inspect, text

from ..core.config import ROOT, settings
from ..core.security import hash_password
from ..models import Config, Content, Course, Enrollment, RAGFragment, RolePermission, User
from ..rag import chunk_text, extract_text
from ..services.storage import get_storage
from .session import SessionLocal, engine
from ..models import Base

DEMO_MATERIALS_DIR = ROOT / "data" / "demo_materials"
DEMO_CATALOG_PATH = DEMO_MATERIALS_DIR / "catalog.json"
DEMO_NAMESPACE = uuid.UUID("3f6b798e-7661-4cb0-a361-e61353d9be12")
FALLBACK_EMBEDDING_MODEL = "fallback-lexical-v1"

PERMISSIONS = {
    "administrador": ["admin:users", "admin:roles", "admin:config", "admin:audit", "course:read", "rag:query"],
    "docente": ["course:read", "course:write", "content:write", "assessment:write", "analytics:read", "rag:query"],
    "estudiante": ["course:read", "rag:query", "assessment:solve"],
}


def create_schema_for_tests(reset: bool = False) -> None:
    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    if engine.dialect.name == 'sqlite' and 'carpeta_id' not in {c['name'] for c in inspect(engine).get_columns('contenidos')}:
        with engine.begin() as connection:
            connection.execute(text(
                'ALTER TABLE contenidos ADD COLUMN carpeta_id CHAR(32) REFERENCES carpetas_contenido(id)'))
    if engine.dialect.name == 'sqlite' and 'descripcion' not in {c['name'] for c in inspect(engine).get_columns('cursos')}:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE cursos ADD COLUMN descripcion TEXT NOT NULL DEFAULT ''"))
    if engine.dialect.name == 'sqlite' and 'alcance' not in {c['name'] for c in inspect(engine).get_columns('conversaciones')}:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE conversaciones ADD COLUMN alcance JSON NOT NULL DEFAULT '{}'"))


def seed_demo_data(force: bool = False) -> None:
    if force:
        return
    with SessionLocal() as db:
        admin = _ensure_demo_user(
            db, "administrador", "Administrador Monda", "admin@monda.local", "Admin123!")
        teacher = _ensure_demo_user(
            db, "docente", "Docente Demo", "docente@monda.local", "Docente123!")
        student = _ensure_demo_user(
            db, "estudiante", "Estudiante Demo", "estudiante@monda.local", "Estudiante123!")
        catalog = json.loads(DEMO_CATALOG_PATH.read_text(encoding="utf-8"))
        course_names = {item["name"] for item in catalog["courses"]}
        legacy_course = db.query(Course).filter_by(
            docente_id=teacher.id, nombre="Introducción a Sistemas").first()
        if legacy_course is not None and legacy_course.nombre not in course_names:
            legacy_course.estado = "archivado"

        for course_data in catalog["courses"]:
            course = db.query(Course).filter_by(
                docente_id=teacher.id, nombre=course_data["name"]).first()
            if course is None:
                course = Course(
                    docente_id=teacher.id,
                    nombre=course_data["name"],
                    descripcion=course_data["description"],
                    estado="activo",
                )
                db.add(course)
                db.flush()
            elif not course.descripcion:
                course.descripcion = course_data["description"]

            enrollment = db.get(
                Enrollment, {"curso_id": course.id, "estudiante_id": student.id})
            if enrollment is None:
                db.add(Enrollment(curso_id=course.id,
                       estudiante_id=student.id, estado="activa"))

            for material_data in course_data["materials"]:
                _ensure_demo_material(
                    db, course, teacher, course_data["slug"], material_data)

        rag_config = db.get(Config, "rag")
        if rag_config is None:
            db.add(Config(clave="rag", valor={"topK": settings.rag_top_k, "umbral": settings.rag_similarity_threshold, "mode": settings.rag_mode,
                   "modelo": settings.gemini_llm_model, "ollamaModel": settings.ollama_llm_model}, version=1, actualizado_por=admin.id))
        if db.get(Config, "alerts") is None:
            db.add(Config(clave="alerts", valor={
                   "inactividadDias": 7, "promedioMinimo": 11}, version=1, actualizado_por=admin.id))
        for role, perms in PERMISSIONS.items():
            for permission in perms:
                if db.get(RolePermission, {"rol": role, "permiso": permission}) is None:
                    db.add(RolePermission(
                        rol=role, permiso=permission, version=1))
        db.commit()


def _ensure_demo_user(db, role: str, name: str, email: str, password: str) -> User:
    user = db.query(User).filter_by(correo=email).first()
    if user is None:
        user = User(rol=role, nombre=name, correo=email,
                    password_hash=hash_password(password), estado="activo")
        db.add(user)
        db.flush()
    return user


def _ensure_demo_material(db, course: Course, teacher: User, course_slug: str, material_data: dict) -> None:
    source_path = DEMO_MATERIALS_DIR / course_slug / material_data["filename"]
    data = source_path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    content_id = str(uuid.uuid5(
        DEMO_NAMESPACE, f"{course_slug}/{material_data['filename']}"))
    document_id = str(uuid.uuid5(
        DEMO_NAMESPACE, f"document/{course_slug}/{material_data['filename']}"))
    content = db.get(Content, content_id)
    if content is not None and content.curso_id != course.id:
        raise ValueError(
            f"El material de demo {material_data['filename']} ya pertenece a otro curso")

    storage_key = f"demo/{content_id}.pdf"
    stored_key = get_storage().put(storage_key, data, "application/pdf")
    if content is None:
        content = Content(
            id=content_id,
            documento_id=document_id,
            curso_id=course.id,
            version=1,
            nombre_original=material_data["filename"],
            mime_type="application/pdf",
            tamano_bytes=len(data),
            s3_key=stored_key,
            hash_sha256=digest,
            autor_id=teacher.id,
            estado_indexacion="pendiente",
            activo=False,
            modelo_embedding="pendiente",
        )
        db.add(content)
        db.flush()

    has_fragments = db.query(RAGFragment.id).filter_by(
        contenido_id=content.id).first() is not None
    rebuild_fragments = content.hash_sha256 != digest or (
        not has_fragments and content.estado_indexacion != "error")
    has_known_extraction_error = not rebuild_fragments and not has_fragments and content.estado_indexacion == "error"
    content.documento_id = document_id
    content.nombre_original = material_data["filename"]
    content.mime_type = "application/pdf"
    content.tamano_bytes = len(data)
    content.s3_key = stored_key
    content.hash_sha256 = digest
    content.autor_id = teacher.id
    chunks = None
    if rebuild_fragments:
        extracted_text, _ = extract_text(get_storage().local_path(stored_key))
        chunks = chunk_text(extracted_text)
        db.query(RAGFragment).filter_by(
            contenido_id=content.id).delete(synchronize_session=False)

    if (rebuild_fragments and not chunks) or has_known_extraction_error:
        content.estado_indexacion = "error"
        content.activo = False
        content.modelo_embedding = "sin-texto-extraible"
    else:
        content.estado_indexacion = "indexado"
        content.activo = True
        content.modelo_embedding = FALLBACK_EMBEDDING_MODEL

    if chunks:
        for ordinal, piece in enumerate(chunks, 1):
            fragment_hash = hashlib.sha256(
                f"{document_id}:1:{ordinal}:{FALLBACK_EMBEDDING_MODEL}:{piece}".encode(
                    "utf-8")
            ).hexdigest()
            db.add(RAGFragment(
                id=str(uuid.uuid5(uuid.UUID(content.id),
                       f"{ordinal}:{FALLBACK_EMBEDDING_MODEL}")),
                contenido_id=content.id,
                curso_id=course.id,
                ordinal=ordinal,
                texto=piece,
                ubicacion=f"fragmento {ordinal}",
                metadata_json={
                    "filename": material_data["filename"], "version": 1},
                embedding=None,
                embedding_model=FALLBACK_EMBEDDING_MODEL,
                embedding_provider="fallback",
                hash_fragmento=fragment_hash,
            ))


def init_test_db(reset: bool = True) -> None:
    create_schema_for_tests(reset=reset)
    seed_demo_data()
