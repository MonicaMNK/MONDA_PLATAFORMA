# Suite tras integrar el commit de Mónica — 2 de noviembre de 2026

**Rama:** `fix/midterm-exam-corrections`. **Commit remoto integrado:** `c40f04f` (`test de endpoint RAG con gemini`). **Comando:** `.venv312\Scripts\python.exe -m pytest -q` desde la raíz del repositorio.

La primera corrida encontró **1 fallo y 28 aprobaciones**. El caso nuevo del seed esperaba los nueve PDF activos e indexados; el catálogo marca uno como `requires_ocr`, por lo que el seed lo deja inactivo, con estado `error` y sin fragmentos para evitar exponer texto ilegible. Se ajustó la prueba para comprobar ocho PDF indexados y el PDF pendiente de OCR. El caso dirigido pasó.

La corrida completa posterior terminó con **29 pruebas aprobadas y 1 advertencia**, sin fallos, en 121,43 segundos. La advertencia procede de la integración `httpx`/`starlette.testclient` de Starlette.

Esta corrida usa el entorno local SQLite. Las evidencias PostgreSQL + pgvector y los recorridos formales PI11/PI12 tienen alcance separado.
