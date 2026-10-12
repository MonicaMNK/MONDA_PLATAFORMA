# Plataforma Monda — repositorio integrado PI6 / PI7 (T6–T9)

Aplicación web educativa con FastAPI, PostgreSQL 16 + pgvector, React, control de acceso por roles y tutor RAG con tres adaptadores. El repositorio conserva el diseño, contratos y diagramas PI7 en `reference_design/` y mantiene el DDL ejecutable versionado con Alembic.

> **Alcance honesto:** la UI React que se sirve sin pasos de compilación está en `frontend/app.js` y `frontend/index.html`. También se incluye el proyecto fuente React + TypeScript + Tailwind/Vite en `frontend/src/`; cuando existe `frontend/dist/`, FastAPI sirve ese build. La compilación TSX no se pudo verificar en el entorno de preparación porque npm no pudo acceder a `registry.npmjs.org` (error de resolución DNS). Las pruebas de backend listadas abajo sí se ejecutaron localmente en el entorno de preparación. Antes de una presentación o despliegue real, ejecuta la instalación/build frontend y el recorrido manual descrito al final.

## Funcionalidades incluidas

- Autenticación, access JWT, refresh rotativo por cookie HttpOnly, CSRF, recuperación de acceso y control de fuerza bruta.
- Roles `administrador`, `docente` y `estudiante`; autorización por curso y matrícula activa.
- Cursos, matrículas sin duplicados, carpetas y subcarpetas por semana, materiales PDF/DOCX versionados, vista previa y descarga autorizada.
- Tutor RAG Gemini / Ollama / fallback léxico, con historial privado por usuario y curso, fuentes, abstención por evidencia insuficiente y correlation ID.
- Evaluaciones: generación de borradores, revisión/aprobación docente obligatoria, publicación, intento único y nota calculada en backend sobre 20.
- Indicadores, alertas explicables, exportación CSV y sincronización idempotente de acciones permitidas.
- PostgreSQL 16 + pgvector; 23 tablas: las 20 estructuras PI7, 2 estructuras operativas y carpetas de materiales. Versiones Alembic.
- Auditoría append-only, OpenAPI y trazas JSONL locales; integración MLflow opcional.
- Adaptador de almacenamiento local y adaptador S3 para migración.

## Requisitos

### Prueba rápida sin Docker (Windows)

Ejecuta `INICIAR_MONDA_LOCAL.bat` y abre http://127.0.0.1:8000.
Este modo usa SQLite persistente y el tutor léxico. Instalación y recorrido completo:
[Prueba local](docs/PRUEBA_LOCAL.md).

- Docker Desktop o Docker Engine + Compose plugin, recomendados para ejecutar PostgreSQL y API.
- Alternativa sin Docker: Python 3.12+, PostgreSQL 16 con extensión pgvector instalada.
- Node.js 20+ y npm solo para compilar el frontend TypeScript/Tailwind. El frontend estático incluido no necesita Node para servirlo.

## Inicio rápido (Docker)

1. Clona el repositorio y entra a la carpeta:

   ```bash
   git clone <URL_DE_TU_REPOSITORIO>
   cd MONDA_PLATAFORMA
   ```

2. Crea la configuración local y cambia la clave de firma por una aleatoria propia:

   ```bash
   cp .env.example .env
   ```

   En `.env`, define `MONDA_SECRET_KEY` con al menos 32 bytes aleatorios. Para modo local, `COOKIE_SECURE=0`; **no uses ese valor detrás de HTTPS en producción**. No introduzcas claves de proveedor en Git.

3. Construye y arranca el conjunto local:

   ```bash
   docker compose up --build -d
   docker compose logs -f app
   ```

   El contenedor de aplicación aplica Alembic, carga los datos demo si `MONDA_DEMO=1` y arranca FastAPI. Para terminarlo: `docker compose down`. Para conservar la base de datos no añadas `-v`; para borrar todos los datos de prueba: `docker compose down -v`.

4. Abre `http://localhost:8000`. API interactiva: `http://localhost:8000/docs`; healthcheck: `http://localhost:8000/api/health`.

### Usuarios de prueba precargados

Solo para entorno local con `MONDA_DEMO=1`:

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@monda.local` | `Admin123!` |
| Docente | `docente@monda.local` | `Docente123!` |
| Estudiante | `estudiante@monda.local` | `Estudiante123!` |

El seed crea el curso **Introducción a Sistemas**, matrícula del estudiante y fragmentos de texto base para probar el tutor en fallback. Los usuarios y las contraseñas son exclusivamente datos sintéticos de desarrollo. Deshabilita seeds y cambia secretos para cualquier entorno compartido.

## Ejecución manual sin Docker Compose completo

Usa una terminal para la base de datos y otra para la API:

```bash
cp .env.example .env
# Arranca únicamente PostgreSQL:
docker compose -f docker-compose.db.yml up -d
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m backend.app.db.bootstrap
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Estos comandos arrancan los procesos únicamente cuando el desarrollador los ejecuta en su máquina. No son necesarios para correr la suite de pruebas automatizadas.

## Configuración del tutor RAG

En `.env` selecciona el modo:

- `RAG_MODE=auto`: elige Gemini si `GEMINI_API_KEY` está configurada; de otro modo usa fallback, si `RAG_ALLOW_FALLBACK=1`.
- `RAG_MODE=gemini`: API de Gemini con `GEMINI_LLM_MODEL=gemini-3.8-flash` y `GEMINI_EMBEDDING_MODEL=gemini-embedding-2` por defecto. El adaptador genera embeddings de 768 dimensiones, compatibles con `vector(768)`, y usa prefijos de recuperación consistentes. Ambos modelos se pueden cambiar mediante variables de entorno; vuelve a validar disponibilidad y dimensiones antes de reindexar.
- `RAG_MODE=ollama`: servicio Ollama ejecutándose en la máquina anfitriona, con `OLLAMA_LLM_MODEL` y `OLLAMA_EMBEDDING_MODEL` descargados previamente.
- `RAG_MODE=fallback`: búsqueda local por términos/frases del material; no llama a proveedor externo y funciona para smoke tests.

Variables clave: `GEMINI_API_KEY`, `GEMINI_LLM_MODEL`, `GEMINI_EMBEDDING_MODEL`, `OLLAMA_BASE_URL`, `OLLAMA_LLM_MODEL`, `OLLAMA_EMBEDDING_MODEL`, `RAG_TOP_K`, `RAG_SIMILARITY_THRESHOLD`, `STORAGE_MODE`, `S3_BUCKET`, `AWS_REGION` y `MLFLOW_TRACKING_URI`. No pongas una API key en código, Dockerfile, logs ni commits. No afirmes que una respuesta es correcta solo porque supera un umbral de similitud; revisa siempre las fuentes.

**Actualización de modelos Gemini (octubre de 2026).** Los nombres históricos `gemini-1.5-flash` y `text-embedding-004` aparecen en versiones anteriores de PI7, pero el ZIP final usa como valores iniciales `gemini-3.8-flash` y `gemini-embedding-2`. Google documenta `gemini-3.8-flash` como modelo estable y recomienda `gemini-embedding-2` para embeddings; para RAG de texto recomienda configurar la instrucción de tarea en el texto, y permite reducir el vector a 768 dimensiones. Referencias oficiales: [Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash), [embeddings Gemini](https://ai.google.dev/gemini-api/docs/embeddings). Si se cambia el modelo de embedding, reindexa todos los materiales: espacios vectoriales de distintos modelos no se deben mezclar.

## Frontend React + TypeScript + Tailwind

La UI estática ya incluida permite arrancar la aplicación local sin instalar herramientas frontend. El proyecto fuente moderno está en `frontend/src/`, con configuración en `frontend/package.json`, `frontend/vite.config.ts` y `frontend/tailwind.config.js`.

Para instalar y compilar en una máquina con acceso a npm:

```bash
cd frontend
npm install
npm run typecheck
npm run build
cd ..
```

El build se guarda en `frontend/dist/`; cuando está presente, FastAPI lo sirve en `/`. Para volver al frontend estático incluido, mueve o elimina `frontend/dist/`. `npm run dev` es opcional para trabajo de interfaz; el proxy de Vite envía `/api` a `http://127.0.0.1:8000`.

## Migraciones y base de datos

- DDL canónico: `bd/schema.sql`.
- Migraciones: `backend/migrations/versions/`.
- Configuración Alembic: `alembic.ini` y `backend/migrations/env.py`.
- Semillas de permisos SQL: `bd/seeds/001_permisos_rol.sql`; el seed demo funcional se encuentra en `backend/app/db/seed.py`.
- DDL y diagramas PI7 históricos: `reference_design/` y `bd/legacy/` para trazabilidad, no como rutas alternativas de migración.

Usa `alembic upgrade head` para aplicar migraciones. No ejecutes el DDL canónico y las migraciones sobre la misma base vacía como dos métodos distintos: ambos definen el esquema; el método operacional recomendado es Alembic.

## Verificaciones automatizadas (sin iniciar servidores)

```bash
python scripts/check_entrega1.py
python scripts/check_entrega2.py
pytest -q
python -m compileall -q backend
alembic upgrade head --sql > /tmp/monda-schema-preview.sql
```

La prueba de integración utiliza la base de datos de pruebas configurada por `tests/conftest.py`. Estas verificaciones no reemplazan pruebas reales contra una instancia PostgreSQL, llamadas a Gemini, servidor Ollama ni pruebas de carga.

## Estructura del repositorio

```text
backend/app/api/v1/routers/  # contrato REST por dominio
backend/app/core/            # configuración, seguridad y middleware
backend/app/db/              # sesión, auditoría, seed
backend/app/models/          # entidades SQLAlchemy
backend/app/services/        # reglas de dominio
backend/app/rag/              # extracción, recuperación y proveedores
backend/migrations/          # Alembic
bd/schema.sql                # esquema PostgreSQL
frontend/                    # UI estática + fuente React/TS/Tailwind
api/openapi.json             # OpenAPI consolidado
reference_design/            # evidencias y anexos PI7
scripts/                     # verificación y empaquetado
 tests/                      # pruebas automatizadas
```

## Preparación para GitHub

1. Revisa `.env` y verifica que no contiene secretos reales. `.env` está excluido por `.gitignore`; versiona solo `.env.example`.
2. Ejecuta los chequeos anteriores.
3. Revisa `git status`, confirma que no se sube ninguna base local ni material privado, y luego:

   ```bash
   git init
   git add .
   git commit -m "Integrar Plataforma Monda PI6 PI7"
   git branch -M main
   git remote add origin <URL_DE_TU_REPOSITORIO>
   git push -u origin main
   ```

También se puede reconstruir un ZIP limpio con `python scripts/package_release.py`.

## Recorrido de prueba sugerido

1. Inicia sesión como docente y selecciona **Introducción a Sistemas**.
2. Consulta los materiales existentes; carga un PDF/DOCX con texto extraíble y verifica el estado de indexación.
3. Pregunta al tutor sobre el texto de un material y comprueba las fuentes. Con una consulta fuera de tema, verifica la abstención si no hay contexto suficiente.
4. Genera una evaluación, revisa los reactivos y aprueba cada uno. Confirma que publicar una evaluación con reactivos no aprobados devuelve conflicto.
5. Inicia sesión como estudiante matriculado, abre una evaluación publicada, resuelve y cierra el intento. La nota sale del servidor; reintentar no crea un segundo intento.
6. Prueba que un estudiante no acceda a un curso ajeno ni a claves de respuesta antes del cierre.
7. Revisa indicadores, exporta CSV y accede al panel administrativo como administrador.

## Seguridad, privacidad y limitaciones

- La demo contiene contraseñas conocidas de laboratorio. Cambia credenciales y secretos antes de exponer la app a una red.
- En local, HTTP y `COOKIE_SECURE=0` permiten probar cookies. En AWS, usa HTTPS/TLS, cookies `Secure`, IAM mínimo privilegio, Secrets Manager/KMS, RDS privado y S3 Block Public Access.
- Evalúa autorización, retención, consentimiento de participantes menores y tratamiento de datos conforme a los requisitos institucionales y normativa aplicable antes de piloto real.
- No incluye OCR de PDF escaneado ni calificación automática de respuestas abiertas.
- El almacenamiento local y el fallback son para desarrollo; producción necesita backups, S3 privado, observabilidad y ensayo de restauración.

Para estrategia de despliegue, ver [`AWS_MIGRATION.md`](AWS_MIGRATION.md). Para decisiones detalladas del diseño, ver `docs/` y `reference_design/`.
