from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...deps import current_user
from ....db.audit import audit
from ....db.session import get_db
from ....models import User, Assessment, Attempt, Course, Enrollment
from ....schemas import ProfilePatch
from ....services.serializers import user_json

router = APIRouter(prefix="/api/users", tags=["Usuarios"])

@router.get("/me")
def me(user: User = Depends(current_user)):
    return user_json(user)

@router.patch("/me")
def patch_me(body: ProfilePatch, user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.nombre = body.nombre
    user.version += 1
    audit(db, user.id, "PROFILE_UPDATE", f"usuario:{user.id}")
    db.commit()
    return user_json(user)


@router.get('/me/grades')
def my_grades(user:User=Depends(current_user),db:Session=Depends(get_db)):
    from .assessments import results_visible,attempt_json
    items=[]
    rows=db.query(Assessment,Course).join(Course,Course.id==Assessment.curso_id).join(Enrollment,Enrollment.curso_id==Course.id).filter(Enrollment.estudiante_id==user.id,Enrollment.estado=='activa',Assessment.estado.in_(['publicada','cerrada'])).all()
    for assessment,course in rows:
        attempt=db.query(Attempt).filter(Attempt.evaluacion_id==assessment.id,Attempt.estudiante_id==user.id).first()
        items.append({'assessmentId':assessment.id,'courseId':course.id,'curso':course.nombre,'titulo':assessment.titulo,'estado':'completada' if attempt and attempt.estado=='cerrado' else 'en_progreso' if attempt else 'pendiente','resultsPublished':results_visible(assessment),'intento':attempt_json(attempt,assessment) if attempt else None})
    return {'items':items}
