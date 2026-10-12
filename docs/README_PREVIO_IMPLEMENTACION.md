# Plataforma Monda — implementación local funcional

Implementación construida a partir de la arquitectura PI6 y el diseño detallado PI7 de T6–T9. Incluye una interfaz React local, API FastAPI, base de datos con el modelo PI7, tutor RAG, evaluación con revisión docente, analítica, administración, auditoría y sincronización idempotente.

## 1. Ejecutar en Windows

1. Instala **Python 3.12 o 3.13**.
2. Descomprime este ZIP en una ruta simple, por ejemplo `C:\Monda`.
3. Haz doble clic en `INICIAR_MONDA.bat`.
4. La primera ejecución crea `.venv` e instala las dependencias.
5. Abre `http://127.0.0.1:8000`.

Si prefieres consola:

```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

En Linux/macOS: `./iniciar_monda.sh`.

## 2. Usuarios de demostración

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@monda.local` | `Admin123!` |
| Docente | `docente@monda.local` | `Docente123!` |
| Estudiante | `estudiante@monda.local` | `Estudiante123!` |

Son **credenciales ficticias locales**. Antes de publicar, cambia las contraseñas, `MONDA_SECRET_KEY`, desactiva `MONDA_DEMO` y usa HTTPS.

## 3. Qué funciona

- **UI-01 Acceso:** inicio de sesión, refresh rotativo, cierre, recuperación y cambio de contraseña.
- **UI-02 Cursos/perfil:** cursos por rol, creación/edición y matrícula.
- **UI-03 Contenidos:** PDF/DOCX de hasta 20 MiB, versión, extracción, fragmentación e indexación local.
- **UI-04 Tutor RAG:** recuperación TF‑IDF/coseno, fuentes, abstención por evidencia, historial y valoración.
- **UI-05 Generación:** crea borradores de reactivos ligados a fragmentos del material.
- **UI-06 Revisión/publicación:** control de versión, aprobación/rechazo y bloqueo de publicación sin revisión.
- **UI-07 Resolución:** intento único, respuestas y calificación 0–20 calculada por servidor.
- **UI-08 Seguimiento:** indicadores, alertas explicables, revisión y exportación CSV seudonimizada.
- **UI-09 Administración:** usuarios, roles, configuración RAG y auditoría.
- **UI-10 Sincronización:** `actionId` idempotente y borradores locales.

La API sigue el contrato de `docs/contrato_api_pi7.md`. El OpenAPI ejecutable también queda disponible en `http://127.0.0.1:8000/docs`.

## 4. Base de datos

Para la prueba más sencilla se usa **SQLite** en `data/monda.db`; al arrancar se crean 22 tablas: las 20 del PI7 más `fragmentos_rag` y `borradores_sync`, necesarias para ejecutar RAG y sincronización local.

Para PostgreSQL 16 usa:

```bash
psql -v ON_ERROR_STOP=1 -d monda -f bd/001_schema_pi7.sql
psql -v ON_ERROR_STOP=1 -d monda -f bd/002_tablas_operativas_rag_sync.sql
```

La implementación SQLAlchemy crea el esquema equivalente de aplicación. Para migrar a RDS define `DATABASE_URL=postgresql+psycopg://...`.

## 5. RAG local

### Modo incluido, sin modelo adicional

Funciona inmediatamente: extrae PDF/DOCX, crea fragmentos, recupera los más similares y construye una respuesta extractiva con fuentes. Conserva el umbral PI7 de **0,35** y se abstiene si no hay evidencia suficiente.

### Modo generativo local con Ollama (opcional)

1. Instala Ollama por separado y descarga un modelo compatible.
2. Arranca Ollama localmente.
3. Define `MONDA_OLLAMA=1` antes de iniciar Monda.
4. En **Administración → Configuración RAG**, indica el nombre del modelo local.

Si Ollama no está disponible, Monda vuelve al modo extractivo sin romper el flujo.

## 6. Pruebas

```bash
pytest -q
```

Las pruebas cubren autenticación, acceso por roles, RAG, generación/revisión/publicación, resolución de evaluación, calificación y administración.

## 7. Estructura

```text
backend/            FastAPI, seguridad, ORM y RAG
frontend/           React local + CSS (sin CDN)
bd/                 DDL PI7 + extensión operativa
data/                SQLite y materiales locales
docs/                contrato, guía AWS y matriz de implementación
reference_design/    anexos PI7 originales: diagramas, API, prototipo y DDL
tests/               pruebas de integración
```

## 8. AWS

Consulta `docs/DESPLIEGUE_AWS.md`. La guía conserva la arquitectura prevista: RDS PostgreSQL, S3, ingesta desacoplada, recuperación vectorial/OpenSearch, Secrets Manager, observabilidad y despliegue HTTPS.

## 9. Alcance académico

Esta implementación permite **probar el artefacto** y preparar PI8/validación. No debe describirse como validación institucional ya realizada. Los datos iniciales son ficticios y los indicadores mostrados no constituyen resultados de investigación.
