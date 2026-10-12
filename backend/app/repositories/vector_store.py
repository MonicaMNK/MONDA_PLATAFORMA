from __future__ import annotations

from sqlalchemy.orm import Session

from ..rag.retrieval import RetrievedFragment, lexical_search, vector_search


class VectorStoreRepository:
    """Puerto de recuperación desacoplado del motor.

    En PostgreSQL usa pgvector cuando existe un vector de consulta; en modo ligero
    usa recuperación léxica sobre los fragmentos autorizados del curso.
    """

    def __init__(self, db: Session):
        self.db = db

    def search(
        self,
        *,
        course_id: str,
        question: str,
        top_k: int,
        query_vector: list[float] | None = None,
        embedding_model: str | None = None,
        embedding_provider: str | None = None,
        content_ids: list[str] | None = None,
    ) -> list[RetrievedFragment]:
        if query_vector is not None:
            if not embedding_model or not embedding_provider:
                raise ValueError("La búsqueda vectorial requiere modelo y proveedor de embeddings")
            rows = vector_search(self.db, course_id, query_vector, top_k, embedding_model, embedding_provider, content_ids)
            if rows:
                return rows
        return lexical_search(self.db, course_id, question, top_k, content_ids)
