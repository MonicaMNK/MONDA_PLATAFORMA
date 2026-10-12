from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .api.v1 import api_router
from .core.config import ROOT, settings
from .core.errors import http_exception_handler
from .core.middleware import CorrelationIdMiddleware
from .db.seed import seed_demo_data


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Las migraciones Alembic crean el esquema. En modo demo solo insertamos seeds si la BD ya existe.
    if settings.demo_mode:
        try:
            seed_demo_data()
        except Exception:
            # No se intenta crear tablas silenciosamente en PostgreSQL: el README exige `alembic upgrade head`.
            pass
    yield


app = FastAPI(
    title="Plataforma Monda",
    version=settings.app_version,
    description="Backend modular PI7: JWT/RBAC, cursos, materiales, RAG triple modo, evaluaciones, seguimiento y auditoría.",
    lifespan=lifespan,
)
app.add_middleware(CorrelationIdMiddleware)
app.add_exception_handler(HTTPException, http_exception_handler)
app.include_router(api_router)

FRONTEND = ROOT / "frontend"
BUILT_FRONTEND = FRONTEND / "dist"
# Si existe un build de Vite, se sirve ese frontend; si no, se usa la UI React
# estática incluida para que el arranque local no dependa de Node/npm.
if (BUILT_FRONTEND / "assets").exists():
    app.mount("/assets", StaticFiles(directory=BUILT_FRONTEND / "assets"), name="assets")
elif (FRONTEND / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")
if (FRONTEND / "vendor").exists():
    app.mount("/vendor", StaticFiles(directory=FRONTEND / "vendor"), name="vendor")

if (BUILT_FRONTEND / "vite-src" / "index.html").exists():
    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(BUILT_FRONTEND / "vite-src" / "index.html")
elif (FRONTEND / "index.html").exists():
    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(FRONTEND / "index.html")

    @app.get("/app.js", include_in_schema=False)
    def app_js():
        return FileResponse(FRONTEND / "app.js", media_type="application/javascript")

    @app.get("/styles.css", include_in_schema=False)
    def styles():
        return FileResponse(FRONTEND / "styles.css", media_type="text/css")
