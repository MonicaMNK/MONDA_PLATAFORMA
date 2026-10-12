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
    ) -> list[RetrievedFragment]:
        if query_vector is not None:
            rows = vector_search(self.db, course_id, query_vector, top_k)
            if rows:
                return rows
        return lexical_search(self.db, course_id, question, top_k)
