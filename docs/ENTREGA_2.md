# Entrega 2 — Backend FastAPI completo

Esta entrega implementa el backend funcional de **Plataforma Monda** sobre la base de datos de la Entrega 1. El objetivo es conservar el contrato PI7, aplicar aislamiento por curso y dejar desacoplados los adaptadores RAG/almacenamiento para la futura migración a AWS.

## 1. Estructura modular

```text
backend/app/
├── api/
│   ├── deps.py                 # JWT y usuario actual
│   └── v1/routers/             # 41 operaciones PI7 + /api/health
├── core/
│   ├── config.py               # variables de entorno
│   ├── errors.py               # error uniforme + correlationId
│   ├── middleware.py           # correlación y tiempo de proceso
│   └── security.py             # bcrypt, JWT y tokens rotativos
├── db/
│   ├── session.py              # SQLAlchemy / search_path monda
│   ├── seed.py                 # usuarios/curso/material de demostración
│   └── audit.py                # bitácora de acciones críticas
├── models/entities.py          # ORM de las 22 tablas
├── repositories/
│   └── vector_store.py         # puerto de búsqueda pgvector/léxica
├── rag/
│   ├── extraction.py           # PDF/DOCX + chunking 512/50
│   ├── retrieval.py            # pgvector o coincidencia ligera
│   └── providers/
│       ├── gemini.py
│       ├── ollama.py
│       └── fallback.py
└── services/
    ├── auth_service.py
    ├── content_service.py
    ├── rag_service.py
    ├── assessment_service.py
    ├── analytics_service.py
    ├── storage.py
    └── tracing.py
```

`backend/main.py`, `backend/database.py`, `backend/security.py` y `backend/rag.py` se conservan únicamente como capas de compatibilidad; la implementación canónica está en `backend/app/`.

## 2. Autenticación y RBAC

- JWT HS256 con access token de 30 minutos.
- Contraseñas con **bcrypt costo 12** en ejecución normal.
- Refresh token aleatorio de 7 días, almacenado como SHA-256 y rotado en cada uso.
- Cookie `HttpOnly`, `SameSite=Strict`; `Secure` controlado por `COOKIE_SECURE`.
- Protección CSRF en refresh/logout.
- Detección de reutilización de refresh: revoca la familia de sesión.
- Recuperación de contraseña de un solo uso y 15 minutos.
- Bloqueo/rate limit local después de 5 intentos fallidos dentro de la ventana configurada.
- RBAC dinámico mediante `permisos_rol` más autorización de objeto/curso.
- Regla del último Administrador activo.

## 3. Cursos, matrículas y materiales

- El Docente solo modifica cursos propios; el Estudiante solo accede a matrículas activas.
- Matrícula única `(curso, estudiante)`.
- Materiales PDF/DOCX de hasta 20 MiB.
- Versionado por `documento_id + version`.
- La versión anterior se mantiene activa hasta que la nueva termine su indexación.
- Extracción de texto para PDF/DOCX y fragmentación en ventanas aproximadas de 512 tokens con solapamiento de 50.
- Almacenamiento local por defecto; adaptador S3 disponible mediante `STORAGE_MODE=s3`.

## 4. Tutor RAG triple modo

### `RAG_MODE=gemini`

- LLM: `GEMINI_LLM_MODEL=gemini-3.8-flash`.
- Embeddings: `GEMINI_EMBEDDING_MODEL=gemini-embedding-2`.
- Dimensión canónica: 768.
- Recuperación: pgvector/HNSW filtrada por `curso_id` y material activo.
- Solo se envían pregunta y fragmentos autorizados al proveedor.

### `RAG_MODE=ollama`

- Generación local con `OLLAMA_LLM_MODEL` (`llama3`, `mistral`, etc.).
- Embeddings locales con `OLLAMA_EMBEDDING_MODEL=nomic-embed-text` (768d recomendado).
- No requiere Internet cuando los modelos ya están descargados.

### `RAG_MODE=fallback`

- No requiere API key ni servidor de modelos.
- Recuperación léxica normalizada sobre los fragmentos del curso.
- Respuesta extractiva y fuentes recuperables.

### `RAG_MODE=auto`

- Usa Gemini si existe `GEMINI_API_KEY`.
- Si no existe, usa fallback ligero.
- Si un proveedor falla y `RAG_ALLOW_FALLBACK=1`, la consulta/generación evita quedar inutilizable y degrada de forma controlada al modo ligero.

Todas las respuestas persisten `sources`, `evidenceSufficient` y `correlationId`. La traza RAG se escribe en `data/traces/rag_traces.jsonl` con proveedor, modelo, latencias, fuentes y tokens cuando el proveedor los reporta. Si se define `MLFLOW_TRACKING_URI` y MLflow está instalado, se registra además una ejecución en MLflow.

## 5. Evaluaciones

- Generación de 1 a 20 reactivos a partir del material del curso.
- En Gemini/Ollama se solicita JSON estructurado; ante falla se genera un borrador extractivo válido para revisión.
- Todo reactivo nace en estado `borrador`.
- La ruta de publicación devuelve **409** si existe un reactivo no aprobado.
- Tras publicar, los reactivos son inmutables en esta versión.
- El Estudiante nunca recibe `clave` ni `justificacion` antes de responder.
- La calificación se calcula exclusivamente en el servidor: `20 × aciertos / total`, redondeado a dos decimales.
- Un intento por estudiante/evaluación; un cierre repetido devuelve el puntaje ya persistido.

## 6. Seguimiento, reportes, auditoría y sincronización

- Indicadores reconciliados desde RDS/PostgreSQL: promedio, intentos cerrados, evaluaciones y utilidad del tutor.
- Sin intentos cerrados, el promedio es `null`; no se convierte ausencia en nota cero.
- Alertas explicables para promedio bajo e inactividad, con evidencia y revisión docente.
- Exportación CSV seudonimizada y neutralización de fórmulas.
- Auditoría con `actor`, `acción`, `objeto`, `resultado` y `correlationId`.
- Sincronización offline idempotente: solo acepta `borrador_personal` y `valoracion`; no admite envío offline de intentos ni cambios de roles.

## 7. Contrato API

- `api/openapi.json`: OpenAPI generado directamente desde la aplicación FastAPI.
- `api/contrato_api.md`: contrato PI7 original conservado.
- Se validan exactamente **41 operaciones PI7**, además de `/api/health`.
- Los placeholders de las rutas coinciden con PI7 (`{courseId}`, `{contentId}`, `{questionId}`, etc.).
- OpenAPI incluye esquema `JWTBearer`.

## 8. Seeds

Después de aplicar Alembic:

```bash
python -m backend.app.db.bootstrap
```

Crea, si la base está vacía:

- `admin@monda.local` / `Admin123!`
- `docente@monda.local` / `Docente123!`
- `estudiante@monda.local` / `Estudiante123!`
- curso `Introducción a Sistemas`
- matrícula del estudiante
- material DOCX de ejemplo ya indexado en modo fallback
- configuración RAG y catálogo de permisos

Estas credenciales son exclusivamente de demostración local.

## 9. Verificación no interactiva realizada

Sin iniciar `uvicorn`, `npm` ni procesos persistentes:

```bash
python scripts/check_entrega1.py
python scripts/check_entrega2.py
pytest -q
python -m compileall -q backend
alembic upgrade head --sql
```

Los tests cubren flujo RAG, revisión obligatoria, publicación, resolución/calificación, RBAC, aislamiento, sincronización idempotente, carga/indexación DOCX y refresh con CSRF.
