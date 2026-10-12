# Base de datos - Entrega 1

La fuente canónica es `bd/schema.sql`: PostgreSQL 16 + pgvector, esquema `monda`, **22 tablas**.

- 20 tablas del diseño PI7: `usuarios`, `cursos`, `matriculas`, `contenidos`, `conversaciones`, `mensajes`, `valoraciones`, `evaluaciones`, `reactivos`, `intentos`, `respuestas`, `eventos`, `alertas`, `auditoria`, `configuracion`, `sesiones`, `recuperaciones`, `permisos_rol`, `sincronizaciones`, `trabajos`.
- 2 tablas de ejecución local: `fragmentos_rag` y `borradores_sync`.

`fragmentos_rag.embedding` usa `vector(768)`. El embedding es nullable para permitir el modo ligero sin IA; Gemini `gemini-embedding-2` y el embedding local recomendado para Ollama se normalizarán a 768 dimensiones en la Entrega 2.

## Vía Alembic (recomendada)

```bash
docker compose -f docker-compose.db.yml up -d
alembic upgrade head
```

## Vía SQL directa

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f bd/schema.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f bd/seeds/001_permisos_rol.sql
```

No se requiere ejecutar ningún servidor web para esta entrega.
