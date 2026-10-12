"""Demo local persistente con SQLite, sin Docker ni migraciones PostgreSQL."""
from __future__ import annotations

import argparse
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    data_dir = ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    from dotenv import load_dotenv
    load_dotenv(data_dir / ".gemini.env", override=False)
    secret_path = data_dir / ".local_secret"
    if not secret_path.exists():
        secret_path.write_text(secrets.token_urlsafe(48), encoding="utf-8")
    # Antes de importar Settings: evita reutilizar una DATABASE_URL de producción.
    os.environ.update({
        "DATABASE_URL": f"sqlite:///{(data_dir / 'monda_local.db').as_posix()}",
        "APP_ENV": "local", "MONDA_DEMO": "1", "COOKIE_SECURE": "0",
        "RAG_MODE": os.getenv("RAG_MODE", "auto"), "RAG_ALLOW_FALLBACK": "1", "STORAGE_MODE": "local",
        "MONDA_SECRET_KEY": secret_path.read_text(encoding="utf-8").strip(),
    })
    from backend.app.db.seed import create_schema_for_tests, seed_demo_data
    from sqlalchemy import inspect, text
    from backend.app.db.session import engine, SessionLocal
    inspector=inspect(engine)
    tables=inspector.get_table_names()
    if ('cursos' in tables and 'descripcion' not in {c['name'] for c in inspector.get_columns('cursos')}) or ('conversaciones' in tables and 'alcance' not in {c['name'] for c in inspector.get_columns('conversaciones')}):
        import sqlite3
        backup_path=data_dir/'monda_local.before_learning_workflow.db'
        if not backup_path.exists():
            with sqlite3.connect(data_dir/'monda_local.db') as source, sqlite3.connect(backup_path) as backup:
                source.backup(backup)
    if 'contenidos' in inspector.get_table_names() and 'carpeta_id' not in {c['name'] for c in inspector.get_columns('contenidos')}:
        import sqlite3
        backup_path=data_dir/'monda_local.before_folders.db'
        if not backup_path.exists():
            with sqlite3.connect(data_dir/'monda_local.db') as source, sqlite3.connect(backup_path) as backup:
                source.backup(backup)
    create_schema_for_tests(reset=False)
    seed_demo_data()
    from backend.app.models import RolePermission
    with SessionLocal() as db:
        if not db.get(RolePermission, {'rol':'administrador', 'permiso':'rag:query'}):
            db.add(RolePermission(rol='administrador', permiso='rag:query', version=1))
            db.commit()
    print("Demo SQLite lista. Los datos se conservan en data/monda_local.db.")
    if args.prepare_only:
        return
    import uvicorn
    print(f"Monda: http://127.0.0.1:{args.port} | API: http://127.0.0.1:{args.port}/docs")
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
