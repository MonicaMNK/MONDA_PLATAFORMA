# Entrega 1 - Estructura y Base de Datos

## Estado

Entrega completada sin levantar servidores persistentes.

## Decisiones aplicadas

1. Se conserva la nomenclatura y las 20 tablas relacionales del diseño PI7.
2. Se agregan `fragmentos_rag` y `borradores_sync` para completar 22 tablas ejecutables.
3. PostgreSQL 16 es la base local objetivo y `pgvector` queda habilitado desde el inicio.
4. `fragmentos_rag` fuerza aislamiento por curso mediante FK compuesta `(contenido_id, curso_id)`.
5. El vector canónico local es de 768 dimensiones; puede quedar `NULL` en modo ligero.
6. Auditoría es append-only mediante trigger.
7. Evaluaciones mantienen restricciones de revisión, intentos y coherencia intento-reactivo del PI7.
8. Alembic separa el modelo base (20 tablas) de la extensión RAG/sync (2 tablas).

## Estructura preparada

```text
backend/
  app/
    api/v1/         # routers en Entrega 2
    core/           # config, seguridad, RBAC
    db/             # sesión, ORM
    models/         # SQLAlchemy
    schemas/        # Pydantic
    repositories/   # persistencia/adaptadores
    services/       # dominio
    rag/            # Gemini/Ollama/Fallback
  migrations/
    env.py
    versions/
bd/
  schema.sql
  seeds/
    001_permisos_rol.sql
frontend/           # se completa en Entrega 3
docs/
scripts/
tests/
```

## Verificación sin servidor

```bash
python scripts/check_entrega1.py
python -m compileall backend/migrations
```

## Arranque de PostgreSQL para prueba manual posterior

```bash
docker compose -f docker-compose.db.yml up -d
alembic upgrade head
```

No se ejecutó `uvicorn`, `npm start`, ni ningún proceso persistente durante la generación de esta entrega.
