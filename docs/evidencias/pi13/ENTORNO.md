# Entorno de ejecución — PI13

**Fecha de congelación:** 2026-11-09  
**Rama:** main  
**Commit:** `c7be36d` (main)  
**Entorno:** local, puerto 8001, Windows 10 10.0.26100 SP0  
**Tag:** `v1.0-pi13` publicado localmente sobre commit `c7be36d` (no publicado al remoto)

## Versiones

| Componente | Versión |
|------------|---------|
| Python | 3.9.0 |
| k6 | v2.3.0 (imagen `grafana/k6:2.3.0`) |
| FastAPI | 0.115.0 |
| SQLAlchemy | 2.0.36 |
| PostgreSQL | 16.4 |
| pgvector | 0.7.0 |
| Alembic | 1.13.2 (head `20261012_0005`) |
| Gemini LLM | `gemini-3.6-flash` |
| Gemini Embedding | `gemini-embedding-2` |
| pytest | 8.4.2 |
| coverage | 7.1.0 |

## Versiones de Python por ejecución

La versión de la tabla anterior (Python 3.9.0) corresponde al entorno declarado para la suite PI13 local con SQLite/fallback. No debe atribuirse automáticamente a todas las corridas del repositorio. Los respaldos de otras ejecuciones registran versiones distintas:

| Ejecución | Python registrado | Evidencia |
|-----------|-------------------|-----------|
| Suite PI13 local SQLite/fallback | 3.9.0 | `ejecuciones-cp.md` |
| Suite PostgreSQL + pgvector del 2026-11-09 | 3.12.16 | `validacion-postgresql-pgvector-2026-11-09.md` |
| Perfiles k6 del 2026-11-09 | 3.12.16 | `resultado-k6-local-2026-11-09.md` |
| Imagen Docker y CI actualmente configurados | 3.12 | `Dockerfile` y `.github/workflows/quality.yml` |

El requisito Python 3.12+ del README describe la configuración recomendada/actual del proyecto. Los registros históricos conservan la versión que consignó cada ejecución; no se reemplazan por una versión común.

## Navegadores probados

| Navegador | Versión | Flujo cubierto |
|-----------|---------|----------------|
| Chrome | 130 | Carga material, consulta RAG con citas, evaluación |
| Edge | 130 | Carga material, consulta RAG con citas, evaluación |
| Firefox | 131 | Carga material, consulta RAG con citas, evaluación |

## Base de datos

- Motor: PostgreSQL 16.4 con pgvector 0.7.0
- URL: `postgresql+psycopg://db.monda.local:5432/monda_e2e_20261109`
- Pool: `DB_POOL_SIZE=30`, `DB_MAX_OVERFLOW=30`
- Migraciones: hasta `20261012_0005`

## Datos semilla

- Usuarios: docente@monda.local, estudiante@monda.local, admin@monda.local
- Cursos: Biología, Historia, Literatura
- PDFs: 9 archivos en `data/demo_materials/` (biologia, historia, literatura)
- Fragmentos: 118 chunks de 512 tokens con 50 de solapamiento
- Banco de calibración: `data/rag_calibration_gemini_abstencion_20261101.json` (100 consultas)
- Banco de evaluación final: `data/rag_validation_100.json` (85 consultas tras eliminar duplicados)

## Restauración del estado entre corridas

Cada corrida de prueba ejecuta `init_test_db(True)` que reconstruye la base de datos de pruebas desde cero con datos semilla deterministas. Las corridas de k6 usan el pool 30/30 y se ejecutan sobre el mismo commit y configuración. Los datos de usuarios (tiempos pareados, SUS, respuestas) son estáticos y se recogen en `data/usuarios/` sin modificación entre corridas.

## Archivos de manifiesto

- `docs/evidencias/pi13/manifest-pi13.json`: generado por `scripts/create_validation_manifest.py` sobre el commit congelado.
- `data/validation_manifest.json`: manifiesto de campaña de aceptación local (42 archivos, hashes SHA-256 verificados).
