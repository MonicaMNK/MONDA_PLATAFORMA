from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...deps import current_user
from ....core.errors import api_error
from ....db.audit import audit
from ....db.session import get_db
from ....models import Course, Enrollment, User
from ....schemas import CourseIn, CoursePatch, EnrollIn, EnrollPatch
from ....services.access import can_access_course, require_permission, teacher_course
from ....services.serializers import course_json, user_json

router = APIRouter(prefix="/api/courses", tags=["Cursos y matrículas"])


@router.get("")
def list_courses(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, user, "course:read")
    q = db.query(Course)
    if user.rol == "docente":
        q = q.filter(Course.docente_id == user.id)
    elif user.rol == "estudiante":
        q = q.join(Enrollment, Enrollment.curso_id == Course.id).filter(Enrollment.estudiante_id == user.id, Enrollment.estado == "activa")
    total = q.count()
    rows = q.order_by(Course.creado_en.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"items": [course_json(c) for c in rows], "page": page, "total": total}


@router.post("", status_code=201)
def create_course(body: CourseIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.rol == "docente":
        require_permission(db, user, "course:write")
        teacher = user
    elif user.rol == "administrador":
        teacher = db.query(User).filter(User.rol == "docente", User.estado == "activo").order_by(User.creado_en).first()
        if not teacher:
            api_error(422, "NO_TEACHER", "No existe un docente activo para asignar el curso.")
    else:
        api_error(403, "FORBIDDEN", "Solo docentes o administradores pueden crear cursos.")
    course = Course(docente_id=teacher.id, nombre=body.nombre, estado="activo")
    db.add(course)
    db.flush()
    audit(db, user.id, "COURSE_CREATE", f"curso:{course.id}")
    db.commit()
    return course_json(course)


@router.patch("/{courseId}")
def patch_course(courseId: str, body: CoursePatch, user: User = Depends(current_user), db: Session = Depends(get_db)):
    course = teacher_course(db, user, courseId)
    if body.nombre is not None:
        course.nombre = body.nombre
    if body.estado is not None:
        if body.estado not in {"activo", "archivado"}:
            api_error(422, "COURSE_STATE", "Estado inválido.")
        course.estado = body.estado
    audit(db, user.id, "COURSE_UPDATE", f"curso:{course.id}")
    db.commit()
    return course_json(course)


@router.post("/{courseId}/enrollments", status_code=201)
def create_enrollment(courseId: str, body: EnrollIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    teacher_course(db, user, courseId)
    student = db.get(User, body.estudianteId)
    if not student or student.rol != "estudiante" or student.estado != "activo":
        api_error(422, "INVALID_STUDENT", "El usuario indicado no es un estudiante activo.")
    existing = db.get(Enrollment, {"curso_id": courseId, "estudiante_id": student.id})
    if existing:
        api_error(409, "ENROLLMENT_EXISTS", "La matrícula ya existe.")
    row = Enrollment(curso_id=courseId, estudiante_id=student.id, estado="activa")
    db.add(row)
    audit(db, user.id, "ENROLLMENT_CREATE", f"curso:{courseId}:estudiante:{student.id}")
    db.commit()
    return {"courseId": courseId, "estudianteId": student.id, "estado": row.estado}


@router.get("/{courseId}/enrollments")
def list_enrollments(courseId: str, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), user: User = Depends(current_user), db: Session = Depends(get_db)):
    teacher_course(db, user, courseId)
    q = db.query(Enrollment).filter(Enrollment.curso_id == courseId)
    total = q.count()
    rows = q.order_by(Enrollment.creado_en.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"items": [{"courseId": e.curso_id, "estudianteId": e.estudiante_id, "estado": e.estado, "estudiante": user_json(db.get(User, e.estudiante_id))} for e in rows], "page": page, "total": total}


@router.patch("/{courseId}/enrollments/{studentId}")
def update_enrollment(courseId: str, studentId: str, body: EnrollPatch, user: User = Depends(current_user), db: Session = Depends(get_db)):
    teacher_course(db, user, courseId)
    row = db.get(Enrollment, {"curso_id": courseId, "estudiante_id": studentId})
    if not row:
        api_error(404, "ENROLLMENT_NOT_FOUND", "Matrícula no encontrada.")
    if body.estado not in {"activa", "inactiva"}:
        api_error(422, "ENROLLMENT_STATE", "Estado inválido.")
    row.estado = body.estado
    audit(db, user.id, "ENROLLMENT_UPDATE", f"curso:{courseId}:estudiante:{studentId}")
    db.commit()
    return {"courseId": courseId, "estudianteId": studentId, "estado": row.estado}
