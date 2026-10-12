from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..core.config import settings

if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif settings.database_url.startswith("postgresql"):
    # El search_path se fija en la conexión misma (opción de arranque del servidor).
    # Un "SET search_path" ejecutado en el evento connect queda dentro de una transacción
    # y se pierde con el primer rollback del pool, por eso el esquema `monda` dejaba de verse.
    connect_args = {"options": "-c search_path=monda,public"}
else:
    connect_args = {}
engine = create_engine(settings.database_url, future=True,
                       pool_pre_ping=True, connect_args=connect_args)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
