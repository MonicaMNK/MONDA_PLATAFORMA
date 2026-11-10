# Inventario de evidencias — PI13

Sección 3.3 de la campaña de aceptación. Todas las rutas son relativas a la raíz del repositorio.

| N.° | Evidencia | Tipo | Caso / Indicador | Ruta |
|-----|-----------|------|------------------|------|
| 1 | Entorno de ejecución PI13 | Markdown | Entorno, versiones, commit | docs/evidencias/pi13/ENTORNO.md |
| 2 | Ejecución de casos CP | CSV | CP01–CP12 | docs/evidencias/pi13/cp-ejecucion.csv |
| 3 | Trazabilidad OE→indicador→CP→evidencia | CSV | Matriz de trazabilidad | docs/evidencias/pi13/trazabilidad.csv |
| 4 | Desviaciones registradas | Markdown | D-01 a D-06 | docs/evidencias/pi13/desviaciones.md |
| 5 | Incidencias de campaña | Markdown | I-01 a I-05 | docs/evidencias/pi13/incidencias.md |
| 6 | Resultado funcional por módulo | Markdown | M1–M8 | docs/evidencias/pi13/resumen-funcional.md |
| 7 | Resultado k6 local | Markdown | RNF-01, CP08 | docs/evidencias/pi13/resultado-k6-local-2026-11-09.md |
| 8 | k6 25 VU pool 30/30 | JSON | RNF-01 | docs/evidencias/pi13/k6-25-vu-pool-30-30-2026-11-09.json |
| 9 | k6 50 VU pool 30/30 | JSON | RNF-01 | docs/evidencias/pi13/k6-50-vu-pool-30-30-2026-11-09.json |
| 10 | Comparación k6 30/30 | JSON | RNF-01 | docs/evidencias/pi13/k6-comparison-pool-30-30-2026-11-09.json |
| 11 | Validación PostgreSQL + pgvector | Markdown | D07, CP11 | docs/evidencias/pi13/validacion-postgresql-pgvector-2026-11-09.md |
| 12 | Recorrido E1-E3 PostgreSQL+Gemini | Markdown | OE1, OE2, OE3 | docs/evidencias/pi13/flujo-e1-e3-postgresql-gemini-2026-11-09.md |
| 13 | Recorrido E2 Gemini browser | Markdown | E2 | docs/evidencias/pi13/flujo-e2-gemini-browser-2026-11-09.md |
| 14 | Latencia RAG | JSON | RNF-02 | data/rag_latency_20261109.json |
| 15 | Banco de evaluación final | JSON | OE2, RNF-02, RNF-08 | data/rag_validation_100.json |
| 16 | Resultados calibración integración | JSON | OE2 | data/rag_calibration_integration_results_20261109.json |
| 17 | Banco calibración integración | JSON | OE2 | data/rag_calibration_integration_20261109.json |
| 18 | Disponibilidad 30 días | Log | RNF-04 | data/availability_probe_30d_20261109.log |
| 19 | Campaña SUS | JSON | RNF-06 | data/sus_campaign_20261109.json |
| 20 | Calificaciones expertos | CSV | Rúbrica fidelidad | data/expert_ratings_20261109.csv |
| 21 | Resumen expertos | JSON | Rúbrica fidelidad | data/expert_ratings_summary_20261109.json |
| 22 | Tiempos pareados | CSV | O4, línea base | data/paired_times_20261109.csv |
| 23 | Resumen tiempos pareados | JSON | O4 | data/paired_time_summary.json |
| 24 | Manifiesto de validación | JSON | Configuración reproducible | data/validation_manifest.json |
| 25 | Umbrales de aceptación | JSON | RNF-01/02/04/05/07/08, OE2 | data/acceptance_thresholds.json |
| 26 | Trazabilidad de aceptación | JSON | OE1, OE2, OE3 | data/acceptance_traceability.json |
| 27 | Evidencia RNF | JSON | RNF-04/05/07 | data/acceptance_evidence_rnf.json |
| 28 | Aprobación de umbrales | JSON | Umbrales revisados 09/11 | data/aprobacion_umbrales_20261109.json |
| 29 | Cobertura de tests | XML | RNF-07 | reports/coverage.xml |
| 30 | Reporte cobertura HTML | HTML | RNF-07 | reports/htmlcov/index.html |
| 31 | Calibración RAG anterior | JSON | Antecedente OE2 | data/rag_calibration_gemini_abstencion_20261101.json |
| 32 | Evaluación live RAG anterior | JSON | Antecedente OE2 | data/rag_gemini_live_20261101.json |
| 33 | Capturas Chrome | PNG (3) | E2-E3 browser | docs/evidencias/captura-chrome-*-20261109.png |
| 34 | Capturas Edge | PNG (3) | E2-E3 browser | docs/evidencias/captura-edge-*-20261109.png |
| 35 | Capturas Firefox | PNG (3) | E2-E3 browser | docs/evidencias/captura-firefox-*-20261109.png |
| 36 | Captura respuesta citada | PNG | E2 | docs/evidencias/captura-e2-gemini-respuesta-citada.png |
| 37 | Captura abstención | PNG | E2 | docs/evidencias/captura-e2-gemini-abstencion.png |
| 38 | Captura respuesta citada E2 | PNG | E2 | docs/evidencias/captura-e2-gemini-respuesta-citada.png |
| 39 | UI E2 Gemini | JSON | E2 | docs/evidencias/e2-gemini-ui-2026-11-09.json |

## Evidencia histórica (docs/evidencias/historico/)

Archivos del 1 de noviembre y versiones anteriores mantenidos únicamente para trazabilidad. No describen el estado actual.
