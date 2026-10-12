from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ...deps import current_user
from ....core.errors import api_error
from ....db.session import get_db
from ....models import Conversation, Message, Rating, User
from ....schemas import RagIn, RatingIn
from ....services.access import can_access_course
from ....services.rag_service import query_rag
from ....services.serializers import dtiso

router = APIRouter(tags=["Tutor RAG"])

@router.post("/api/courses/{courseId}/rag/query")
def rag_query(courseId: str, body: RagIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return query_rag(db, user, courseId, body.question, body.conversationId)

@router.get("/api/rag/conversations")
def conversations(courseId: str, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), user: User = Depends(current_user), db: Session = Depends(get_db)):
    can_access_course(db, user, courseId)
    q = db.query(Conversation).filter(Conversation.curso_id == courseId)
    if user.rol == "estudiante":
        q = q.filter(Conversation.usuario_id == user.id)
    elif user.rol == "docente":
        # El docente propietario puede revisar conversaciones del curso para seguimiento pedagógico.
        pass
    total = q.count()
    rows = q.order_by(Conversation.creado_en.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"items": [{"id": c.id, "courseId": c.curso_id, "usuarioId": c.usuario_id if user.rol != "estudiante" else None, "estado": c.estado, "creadoEn": dtiso(c.creado_en)} for c in rows], "page": page, "total": total}

@router.get("/api/rag/conversations/{conversationId}/messages")
def conversation_messages(conversationId: str, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=100), user: User = Depends(current_user), db: Session = Depends(get_db)):
    conv = db.get(Conversation, conversationId)
    if not conv:
        api_error(404, "CONVERSATION_NOT_FOUND", "Conversación no encontrada.")
    can_access_course(db, user, conv.curso_id)
    if user.rol == "estudiante" and conv.usuario_id != user.id:
        api_error(403, "FORBIDDEN", "Conversación no autorizada.")
    q = db.query(Message).filter(Message.conversacion_id == conversationId)
    total = q.count()
    rows = q.order_by(Message.creado_en.asc()).offset((page - 1) * limit).limit(limit).all()
    return {"items": [{"id": m.id, "autor": m.autor, "contenido": m.contenido, "fuentes": m.fuentes, "evidenceSufficient": m.evidencia_suficiente, "creadoEn": dtiso(m.creado_en)} for m in rows], "page": page, "total": total}

@router.post("/api/rag/messages/{messageId}/rating")
def rate_message(messageId: str, body: RatingIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    message = db.get(Message, messageId)
    if not message or message.autor != "tutor":
        api_error(404, "MESSAGE_NOT_FOUND", "Mensaje del tutor no encontrado.")
    conv = db.get(Conversation, message.conversacion_id)
    if conv.usuario_id != user.id:
        api_error(403, "FORBIDDEN", "Solo el propietario puede valorar la respuesta.")
    rating = db.query(Rating).filter(Rating.mensaje_id == message.id, Rating.usuario_id == user.id).first()
    created = rating is None
    if rating is None:
        rating = Rating(mensaje_id=message.id, usuario_id=user.id, util=body.util, comentario=body.comentario)
        db.add(rating)
    else:
        rating.util = body.util
        rating.comentario = body.comentario
    db.commit()
    return {"ratingId": rating.id, "util": rating.util, "created": created}
