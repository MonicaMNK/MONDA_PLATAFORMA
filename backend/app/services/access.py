from __future__ import annotations

from sqlalchemy.orm import Session

from ..core.errors import api_error
from ..models import Course, Enrollment, RolePermission, User


def has_permission(db: Session, user: User, permission: str) -> bool:
    return db.query(RolePermission).filter(RolePermission.rol == user.rol, RolePermission.permiso == permission).first() is not None


def require_permission(db: Session, user: User, permission: str) -> None:
    if not has_permission(db, user, permission):
        api_error(403, "FORBIDDEN", f"El rol {user.rol} no tiene el permiso requerido: {permission}.")


def course_or_404(db: Session, course_id: str) -> Course:
    course = db.get(Course, course_id)
    if not course:
        api_error(404, "COURSE_NOT_FOUND", "Curso no encontrado.")
    return course


def can_access_course(db: Session, user: User, course_id: str, write: bool = False) -> Course:
    course = course_or_404(db, course_id)
    if user.rol == "administrador":
        return course
    if user.rol == "docente" and course.docente_id == user.id:
        return course
    if not write and user.rol == "estudiante":
        enrollment = db.get(Enrollment, {"curso_id": course_id, "estudiante_id": user.id})
        if enrollment and enrollment.estado == "activa":
            return course
    api_error(403, "COURSE_FORBIDDEN", "No tienes acceso a este curso.")


def teacher_course(db: Session, user: User, course_id: str) -> Course:
    require_permission(db, user, "course:write") if user.rol != "administrador" else None
    course = course_or_404(db, course_id)
    if user.rol == "administrador" or (user.rol == "docente" and course.docente_id == user.id):
        return course
    api_error(403, "TEACHER_REQUIRED", "La operación requiere al docente propietario del curso.")
