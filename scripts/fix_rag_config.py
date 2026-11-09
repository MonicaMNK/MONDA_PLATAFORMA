"""Script para corregir la fila `rag` de la tabla Config en la BD local.

Uso:
  python scripts/fix_rag_config.py

Este script:
1. Crea el esquema si no existe (usando SQLAlchemy).
2. Ejecuta el seed demo (que solo añade la fila rag si no existe).
3. Corrige la fila rag existente para que quede topK=1, umbral=0.69
   (los defaults de settings), actualizando version y auditoría.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal, engine
from backend.app.models import Base, Config, User
from backend.app.db.seed import seed_demo_data, create_schema_for_tests


def fix_rag_config() -> None:
    # 1. Crear esquema si no existe
    Base.metadata.create_all(bind=engine)

    # 2. Sembrar datos demo (crea la fila rag solo si no existe)
    seed_demo_data()

    # 3. Forzar valores correctos en la fila rag
    with SessionLocal() as db:
        row = db.get(Config, "rag")
        if row is None:
            # El seed no la creó (por ejemplo, force=False en un entorno sin demo)
            admin = db.query(User).filter_by(rol="administrador").first()
            admin_id = admin.id if admin else 1
            row = Config(clave="rag", valor={}, version=1, actualizado_por=admin_id)
            db.add(row)
            db.flush()

        valor = dict(row.valor or {})
        changed = False
        if valor.get("topK") != settings.rag_top_k:
            valor["topK"] = settings.rag_top_k
            changed = True
        if valor.get("umbral") != settings.rag_similarity_threshold:
            valor["umbral"] = settings.rag_similarity_threshold
            changed = True
        if changed:
            row.valor = valor
            row.version += 1
            db.commit()
            print(f"[fix_rag_config] Fila rag actualizada: topK={valor['topK']}, umbral={valor['umbral']}, version={row.version}")
        else:
            print(f"[fix_rag_config] La fila rag ya está correcta: topK={valor['topK']}, umbral={valor['umbral']}")


if __name__ == "__main__":
    fix_rag_config()