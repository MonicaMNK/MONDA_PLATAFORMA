# Registro de ejecuciones — Casos de prueba PI13

Cada entrada documenta una ejecución individual con fecha, ejecutor, entorno, resultado y evidencia.

## CP01 — ES01: Docente sube PDF y lo indexa
- Fecha: 2026-11-09
- Ejecutor: Daniel
- Entorno: local, puerto 8001, SQLite, Python 3.9.0
- Resultado: Logrado
- Prueba ejecutada: tests/test_entrega2_backend.py::test_material_upload_version_and_index_fallback
- Evidencia: 78/78 pruebas de backend aprobadas; PDF indexado y recuperable mediante RAG con citas

## CP02 — ES02: Consulta RAG con citas sobre PDF indexado
- Fecha: 2026-11-09
- Ejecutor: Mónica
- Entorno: local, puerto 8001, modo fallback, Gemini 3.6-flash
- Resultado: Logrado
- Prueba ejecutada: tests/test_entrega2_backend.py::test_full_pi7_backend_flow_fallback_rag
- Evidencia: Respuesta generada con citas PDF válidas; 409 REVIEW_REQUIRED antes de aprobación

## CP03 — ES03: Estudiante no puede publicar borrador de docente
- Fecha: 2026-11-09
- Ejecutor: Mónica
- Entorno: local, puerto 8001, SQLite
- Resultado: Logrado
- Prueba ejecutada: tests/test_pi11_es06_es10.py::test_es06_student_cannot_publish_teacher_draft
- Evidencia: Respuesta HTTP 403 al intento de publicación por estudiante

## CP04 — ES04: Estudiante no puede acceder a admin
- Fecha: 2026-11-09
- Ejecutor: Daniel
- Entorno: local, puerto 8001, SQLite
- Resultado: Logrado
- Prueba ejecutada: tests/test_entrega2_backend.py::test_course_isolation_and_rbac
- Evidencia: Respuesta HTTP 403 en ambos casos (curso ajeno y panel admin)

## CP05 — ES05: Nota 6.67/20 con 1 de 3 reactivos + sin intentos cerrados no hay alerta
- Fecha: 2026-11-09
- Ejecutor: Mónica
- Entorno: local, puerto 8001, SQLite
- Resultado: Logrado
- Prueba ejecutada: tests/test_learning_workflow.py::test_es05_uno_de_tres_reactivos_califica_6_67_y_sin_intentos_cerrados_no_alerta
- Evidencia: Calificación 6.67/20 correcta con 1 de 3 reactivos; 0 alertas con 0 intentos cerrados

## CP06 — ES06: OE3: promedio 10 y 14 = 12, no activa alerta baja
- Fecha: 2026-11-09
- Ejecutor: Mónica
- Entorno: local, puerto 8001, SQLite
- Resultado: Logrado
- Prueba ejecutada: tests/test_learning_workflow.py::test_cp_oe3_average_10_and_14_is_12_and_does_not_trigger_low_alert
- Evidencia: Promedio 12.0 sin activar alerta baja; 0 alertas con 0 intentos cerrados

## CP07 — ES07: Sincronización aplica una vez y rechaza acciones inseguras
- Fecha: 2026-11-09
- Ejecutor: Daniel
- Entorno: local, puerto 8001, SQLite
- Resultado: Logrado
- Prueba ejecutada: tests/test_pi11_es06_es10.py::test_es10_sync_api_applies_once_and_rejects_unsafe_actions
- Evidencia: Sincronización aplicada una sola vez; acciones inseguras rechazadas con error

## CP08 — RNF-01: p95 <= 800 ms a 50 VU, degradación <= 20%
- Fecha: 2026-11-09 (dos ejecuciones: 25 VU y 50 VU)
- Ejecutor: Daniel
- Entorno: local, k6 v2.3.0, pool 30/30
- Resultado: Logrado
- Evidencia: docs/evidencias/resultado-k6-local-2026-11-09.md
- Valores: p95 25 VU = 739.61 ms; p95 50 VU = 785.40 ms; errores HTTP = 0%; degradación = 6.19%

## CP09 — RNF-02: latencia RAG mediana <= 3000 ms y p95 <= 5000 ms
- Fecha: 2026-11-09
- Ejecutor: Mónica
- Entorno: local, 100 consultas, Gemini 3.6-flash
- Resultado: Parcial
- Evidencia: data/rag_latency_20261109.json
- Valores: mediana 1396.55 ms (logrado <= 3000 ms); p95 55732.48 ms (no logrado <= 5000 ms)

## CP10 — RNF-03: pruebas negativas por rol y curso
- Fecha: 2026-11-09
- Ejecutor: Daniel
- Entorno: local, puerto 8001, SQLite
- Resultado: Logrado
- Prueba ejecutada: tests/test_entrega2_backend.py::test_course_isolation_and_rbac
- Evidencia: HTTP 403 en acceso a curso ajeno y panel de administración

## CP11 — D07: Entorno PostgreSQL + pgvector disponible
- Fecha: 2026-11-09
- Ejecutor: Daniel
- Entorno: local, PostgreSQL 16.4 + pgvector 0.7.0
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/ENTORNO.md

## CP12a — RNF-05: Lighthouse accesibilidad >= 90
- Fecha: 2026-11-09
- Ejecutor: Daniel
- Entorno: local, puerto 8001, Chrome 130 (Headless), Lighthouse 11.3.0
- Resultado: Logrado (score 92 >= 90)
- Evidencia: docs/evidencias/pi13/lighthouse/lighthouse-20261109.json (28 auditorías)

## CP12b — RNF-06: SUS media >= 68
- Fecha: 2026-11-09
- Ejecutor: Daniel
- Entorno: local, 10 participantes (6 docentes, 4 estudiantes)
- Resultado: Logrado (media 86.25 >= 68)
- Evidencia: data/sus_scores.json

## CP12c — RNF-07: cobertura de tests pytest --cov >= 80%
- Fecha: 2026-11-09
- Ejecutor: Daniel
- Entorno: local, Python 3.9.0, pytest 8.4.2, coverage 7.1.0
- Resultado: Logrado (84.2% >= 80%)
- Evidencia: reports/coverage.xml
