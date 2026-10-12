# Consolidación final para GitHub

Esta carpeta incorpora el ZIP original PI7 y los cambios de las entregas 1 y 2, además de la guía de puesta en marcha, guía de migración AWS, estructura fuente React/TypeScript/Tailwind, workflow de calidad y script para construir un ZIP limpio.

## Comprobaciones ejecutadas en el entorno de preparación

- `python scripts/check_entrega1.py`: OK; 22 tablas relacionales/operativas declaradas, pgvector/HNSW y auditoría append-only.
- `python scripts/check_entrega2.py`: OK; 41 operaciones del contrato PI7 más health.
- `pytest -q`: 6 pruebas pasadas.
- `python -m compileall -q backend`: OK.
- `alembic upgrade head --sql`: OK; produce las 22 tablas de aplicación y la tabla de versión Alembic.
- `node --check frontend/app.js`: OK.
- Transpilación sintáctica TypeScript/TSX con el compilador TypeScript del entorno: OK.
- Prueba de instalación/build de Vite: no disponible; `npm install` expiró al no resolver `registry.npmjs.org` (EAI_AGAIN). Por tanto, no se afirma que el bundle TypeScript/Tailwind haya sido construido ni se incluye un `package-lock.json` generado.
- No se inició Uvicorn, `npm start`, Docker Compose ni ningún servidor persistente para las verificaciones.

La ruta local recomendada es `docker compose up --build -d`, que sirve la interfaz React estática incluida con FastAPI y usa el modo fallback por defecto cuando no hay API key. La compilación del frontend moderno se hace separadamente desde `frontend/` en una máquina que tenga acceso al registry npm. Las pruebas automatizadas no sustituyen el recorrido manual en navegador, pruebas contra PostgreSQL real, llamadas reales a Gemini/Ollama, pruebas de carga ni ensayos de backup/restore en AWS.
