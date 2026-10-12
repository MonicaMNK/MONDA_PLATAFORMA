from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...deps import current_user
from ....db.audit import audit
from ....db.session import get_db
from ....models import User
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
