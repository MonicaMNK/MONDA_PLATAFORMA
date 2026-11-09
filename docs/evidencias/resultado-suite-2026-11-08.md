# Resultado de la suite local — 8 de noviembre de 2026

**Commit evaluado:** `b2f89ab` (`fix(perf): resolve thresholds from repository root`).  
**Comando:** `.venv312/Scripts/python.exe -m pytest -q`.  
**Entorno:** Windows, Python 3.12.16, pytest 9.2.0, base de pruebas SQLite.  
**Resultado:** 78 pruebas aprobadas, 0 fallidas, 1 advertencia; 131,40 segundos.

La advertencia corresponde a la deprecación de Starlette por el uso de `httpx` con `TestClient`. La corrida cubre pruebas automatizadas y escenarios sintéticos. No ejecutó PostgreSQL + pgvector, llamadas reales a Gemini, el banco final de 100 consultas ni k6.

Los resultados 25/25 de SQLite y PostgreSQL documentados para el 1 de noviembre corresponden a otra versión y se conservan como evidencia histórica; esta corrida de 76 casos no los reemplaza ni afirma que PostgreSQL se haya repetido.
