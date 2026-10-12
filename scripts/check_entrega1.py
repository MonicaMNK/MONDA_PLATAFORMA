from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
schema = (ROOT / "bd" / "schema.sql").read_text(encoding="utf-8")
expected = [
    "usuarios", "cursos", "matriculas", "contenidos", "conversaciones",
    "mensajes", "valoraciones", "evaluaciones", "reactivos", "intentos",
    "respuestas", "eventos", "alertas", "auditoria", "configuracion",
    "sesiones", "recuperaciones", "permisos_rol", "sincronizaciones", "trabajos",
    "fragmentos_rag", "borradores_sync", "carpetas_contenido",
]
found = re.findall(r"CREATE TABLE IF NOT EXISTS\s+([a-z_]+)\s*\(", schema, flags=re.I)
if found != expected:
    raise SystemExit(f"ERROR: tablas esperadas={expected}\nTablas encontradas={found}")

required_tokens = [
    "CREATE EXTENSION IF NOT EXISTS vector",
    "embedding vector(768)",
    "USING hnsw",
    "auditoria_inmutable",
    "FOREIGN KEY (contenido_id, curso_id)",
]
for token in required_tokens:
    if token not in schema:
        raise SystemExit(f"ERROR: falta marcador requerido: {token}")

versions = sorted((ROOT / "backend" / "migrations" / "versions").glob("*.py"))
if len(versions) < 2:
    raise SystemExit(f"ERROR: se esperaban al menos 2 revisiones Alembic; encontradas={len(versions)}")

print("OK Entrega 1")
print(f"- {len(found)} tablas: {', '.join(found)}")
print("- pgvector + HNSW configurados")
print("- auditoria append-only configurada")
print(f"- {len(versions)} revisiones Alembic presentes")
