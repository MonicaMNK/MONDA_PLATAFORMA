# Registro de ejecuciones — Casos de prueba PI13

Cada entrada documenta una ejecución individual con fecha, ejecutor, entorno, resultado y evidencia.

## CP01 — ES03: Consulta RAG con citas trazables
- Fecha: 2026-11-09
- Ejecutor: Daniel
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp01-evidencia.json
- Prueba: tests/test_entrega2_backend.py::test_full_pi7_backend_flow_fallback_rag

## CP02 — ES02: Acceso denegado a material de curso ajeno
- Fecha: 2026-11-09
- Ejecutor: Daniel
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp02-evidencia.json
- Prueba: tests/test_entrega2_backend.py::test_course_isolation_and_rbac

## CP03 — ES04: Abstención cuando no hay evidencia suficiente
- Fecha: 2026-11-09
- Ejecutor: Daniel
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp03-evidencia.json
- Prueba: tests/test_entrega2_backend.py::test_full_pi7_backend_flow_fallback_rag

## CP04 — ES04: Abstención y defensa frente a inyección de instrucciones (subconjunto RAG)
- Fecha: 2026-11-16
- Ejecutor: Daniel y Mónica
- Revision general: Daniel (tesista); no se modificaron puntajes.
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp04-evidencia.json
- Banco: data/rag_validation_100.json (subconjunto de 15 sin evidencia + 13 adversariales = 28 controles)
- Criterios aplicados: data/pi12_rag_criteria_proporcional.json (modo proporcional N=85)
- Métricas esperadas: abstención correcta ≥14/15; adversariales 13/13
- Nota: ejecutado sobre el banco de 85 consultas; no aplica denominador original de 15 adversariales.

## CP05 — ES05: Evaluación y nota sobre veinte
- Fecha: 2026-11-09
- Ejecutor: Mónica
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp05-evidencia.json
- Prueba: tests/test_learning_workflow.py::test_es05_uno_de_tres_reactivos_califica_6_67_y_sin_intentos_cerrados_no_alerta

## CP06 — ES06: Estudiante no puede publicar evaluación
- Fecha: 2026-11-09
- Ejecutor: Mónica
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp06-evidencia.json
- Prueba: tests/test_pi11_es06_es10.py::test_es06_student_cannot_publish_teacher_draft

## CP07 — ES07: Evaluación final RAG con banco independiente
- Fecha: 2026-11-16
- Ejecutor: Daniel y Mónica
- Revision general: Daniel (tesista); no se modificaron puntajes.
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp07-evidencia.json
- Banco: data/rag_validation_100.json (N=85: 37 factuales, 20 integración, 15 sin evidencia, 13 adversariales)
- Criterios aplicados: data/pi12_rag_criteria_proporcional.json (modo proporcional N=85)
- Métricas esperadas: cobertura ≥49/57 respondibles; citas ≥95%; abstención ≥14/15; fidelidad ≥4/5; adversariales 13/13
- Nota: cambio de N=100 a N=85 registrado como desviación metodológica con regla proporcional congelada; no se presenta como equivalente directo a PI12.

## CP08 — ES08: Carga transaccional con cincuenta usuarios
- Fecha: 2026-11-09 (dos ejecuciones: 25 VU y 50 VU)
- Ejecutor: Daniel
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp08-evidencia.json
- Valores: p95 25 VU = 739.61 ms; p95 50 VU = 785.40 ms; errores HTTP = 0%; degradación = 6.19%

## CP09 — ES09: Tareas con usuarios y SUS
- Fecha: 2026-11-06
- Ejecutor: Daniel y Mónica
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp09-evidencia.json
- Sesión vigente: S-01 (n=16)
- Datos: data/usuarios/tiempos_pareados.csv, data/usuarios/sesiones.csv, docs/evidencias/sesion-usuarios/logs/S-01_log.txt

## CP10 — ES10: Sincronización tras desconexión
- Fecha: 2026-11-09
- Ejecutor: Daniel
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp10-evidencia.json
- Prueba: tests/test_pi11_es06_es10.py::test_es10_sync_api_applies_once_and_rejects_unsafe_actions

## CP11 — ES11: D07 recorrido E1–E3 en PostgreSQL y pgvector
- Fecha: 2026-11-16
- Ejecutor: Daniel
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp11-evidencia.json
- Soporte: docs/evidencias/validacion-postgresql-pgvector-2026-11-09.md y docs/evidencias/pi13/ENTORNO.md

## CP12 — ES01: Acceso permitido a material autorizado
- Fecha: 2026-11-16
- Ejecutor: Daniel
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp12-evidencia.json
- Prueba: tests/test_entrega2_backend.py::test_course_isolation_and_rbac

## CP13 — ES12: Acceso administrativo denegado al estudiante
- Fecha: 2026-11-09
- Ejecutor: Daniel
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp13-evidencia.json
- Prueba: tests/test_entrega2_backend.py::test_course_isolation_and_rbac

## CP14 — ES13: Promedio de dos notas: diez y catorce
- Fecha: 2026-11-09
- Ejecutor: Mónica
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp14-evidencia.json
- Prueba: tests/test_learning_workflow.py::test_cp_oe3_average_10_and_14_is_12_and_does_not_trigger_low_alert

## CP15 — ES14: Latencia del tutor RAG
- Fecha: 2026-11-16
- Ejecutor: Mónica
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp15-evidencia.json
- Soporte: data/rag_latency_20261109.json + medición optimizada bajo configuración congelada PI13

## CP16 — ES15: Accesibilidad con Lighthouse
- Fecha: 2026-11-16
- Ejecutor: Daniel
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp16-evidencia.json
- Soporte: docs/evidencias/pi13/lighthouse/lighthouse-20261109.json

## CP17 — ES16: Cobertura de pruebas
- Fecha: 2026-11-09
- Ejecutor: Daniel
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp17-evidencia.json
- Soporte: reports/coverage.xml

## CP18 — ES17: Publicación bloqueada antes de revisión
- Fecha: 2026-11-16
- Ejecutor: Mónica
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp18-evidencia.json
- Prueba: tests/test_entrega2_backend.py::test_full_pi7_backend_flow_fallback_rag

## CP19 — ES18: Ausencia de alerta sin intentos cerrados
- Fecha: 2026-11-16
- Ejecutor: Mónica
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp19-evidencia.json
- Prueba: tests/test_learning_workflow.py::test_low_average_alert_requires_closed_attempts_and_uses_configured_threshold

## CP20 — ES19: Alerta por promedio inferior al umbral
- Fecha: 2026-11-16
- Ejecutor: Mónica
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp20-evidencia.json
- Prueba: tests/test_learning_workflow.py::test_low_average_alert_requires_closed_attempts_and_uses_configured_threshold

## CP21 — ES20: Exportación denegada a docente ajeno
- Fecha: 2026-11-16
- Ejecutor: Daniel
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp21-evidencia.json
- Prueba: tests/test_admin_management.py::test_admin_creates_edits_users_and_assigns_courses

## CP22 — ES21: Carga e indexación de DOCX
- Fecha: 2026-11-16
- Ejecutor: Daniel
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp22-evidencia.json
- Prueba: tests/test_content_formats.py::test_docx_upload_extracts_and_indexes_text

## CP23 — ES22: PDF escaneado que requiere OCR
- Fecha: 2026-11-16
- Ejecutor: Daniel
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp23-evidencia.json
- Prueba: tests/test_content_formats.py::test_scanned_pdf_returns_specific_ocr_required_status

## CP24 — ES23: Disponibilidad durante treinta días
- Fecha: 2026-11-16
- Ejecutor: Daniel
- Resultado: Logrado
- Evidencia: docs/evidencias/pi13/cp24-evidencia.json
- Soporte: data/availability_probe_30d_20261109.log