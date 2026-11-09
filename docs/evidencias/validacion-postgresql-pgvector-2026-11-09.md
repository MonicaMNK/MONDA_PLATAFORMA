# Validación PostgreSQL y pgvector — 9 de noviembre de 2026

- **Instancia:** PostgreSQL 16.15 en Docker Desktop local; extensión pgvector 0.8.7.
- **Migraciones:** `alembic upgrade head` completó y `alembic current` confirmó `20261012_0005 (head)`.
- **Suite:** `.venv312/Scripts/python.exe -m pytest -q --basetemp=data/.pytest-postgres-pgvector-run2`, con `DATABASE_URL` apuntando a PostgreSQL. Resultado: **78 aprobadas, 0 fallidas, 1 advertencia**, 139.70 s.
- **Comparación SQLite:** la evidencia del 8 de noviembre registra **78 aprobadas, 0 fallidas, 1 advertencia**, 131.40 s. La advertencia en ambas corridas corresponde a la deprecación de Starlette/httpx.

La corrida se hizo en una base local recién creada con el contenedor del proyecto. La prueba de migración y la suite no usaron una instancia productiva.
