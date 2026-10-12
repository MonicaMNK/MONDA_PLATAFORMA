# Verificación de la entrega

Fecha de preparación: 4 de octubre de 2026.

Comprobaciones ejecutadas antes de empaquetar:

- `python -m py_compile backend/*.py` — correcto.
- `node --check frontend/app.js` — correcto.
- `pytest -q` — **2 pruebas aprobadas**.
- Base limpia posterior a pruebas — 3 usuarios demo, 1 curso, 1 material, 4 fragmentos RAG y **22 tablas**.
- Flujo de integración cubierto por pruebas: login docente → consulta RAG con evidencia → generación → bloqueo de publicación sin revisión → aprobación → publicación → login estudiante → intento → calificación → consulta administrativa.
- Pruebas de autorización: estudiante no puede crear cursos ni consultar administración.

El ZIP conserva los anexos PI7 de referencia dentro de `reference_design/`, pero la ejecución usa el código de `backend/` y `frontend/`.
