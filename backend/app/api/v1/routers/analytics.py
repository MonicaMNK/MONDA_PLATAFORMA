from __future__ import annotations

import io
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ...deps import current_user
from ....core.errors import api_error
from ....db.audit import audit
from ....db.session import get_db
from ....models import Alert, User
from ....schemas import AlertPatch
from ....services.access import teacher_course
from ....services.analytics_service import analytics, export_csv
from ....services.serializers import dtiso

router = APIRouter(tags=["Seguimiento y reportes"])

@router.get("/api/courses/{courseId}/analytics")
def course_analytics(courseId: str, desde: datetime | None = None, hasta: datetime | None = None, corte: datetime | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return analytics(db, user, courseId, desde, hasta, corte)

@router.patch("/api/alerts/{alertId}")
def patch_alert(alertId: str, body: AlertPatch, user: User = Depends(current_user), db: Session = Depends(get_db)):
    alert = db.get(Alert, alertId)
    if not alert:
        api_error(404, "ALERT_NOT_FOUND", "Alerta no encontrada.")
    teacher_course(db, user, alert.curso_id)
    if body.estado != "revisada":
        api_error(422, "ALERT_STATE_INVALID", "Solo puede transicionarse a revisada.")
    if alert.estado == "revisada":
        api_error(409, "ALREADY_REVIEWED", "La alerta ya fue revisada.")
    alert.estado = "revisada"
    alert.revisado_por = user.id
    alert.fecha_revision = datetime.now(timezone.utc)
    alert.evidencia = {**(alert.evidencia or {}), "comentarioRevision": body.comentario}
    audit(db, user.id, "ALERT_REVIEW", f"alerta:{alert.id}")
    db.commit()
    return {"id": alert.id, "estado": alert.estado, "revisadoPor": alert.revisado_por, "fechaRevision": dtiso(alert.fecha_revision)}

@router.get("/api/courses/{courseId}/reports/export")
def report_export(courseId: str, desde: datetime | None = None, hasta: datetime | None = None, corte: datetime | None = None, format: str = "csv", user: User = Depends(current_user), db: Session = Depends(get_db)):
    if format != "csv":
        api_error(422, "FORMAT_INVALID", "Solo CSV está habilitado.")
    data = export_csv(db, user, courseId, desde, hasta, corte)
    headers = {"Content-Disposition": f'attachment; filename="monda_reporte_{courseId[:8]}.csv"'}
    return StreamingResponse(io.BytesIO(data), media_type="text/csv", headers=headers)
