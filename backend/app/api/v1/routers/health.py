from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from ....core.config import settings
from ....db.session import get_db

router = APIRouter(tags=["Sistema"])

@router.get("/api/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version, "database": db.bind.dialect.name if db.bind else "unknown", "ragMode": settings.rag_mode, "time": datetime.now(timezone.utc).isoformat()}
