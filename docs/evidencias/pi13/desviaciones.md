# Desviaciones — PI13

## D-01: Cambio de umbrales RAG (09/11/2026)

**Campo:** `rag_top_k` y `rag_similarity_threshold`  
**Valor anterior:** `k=1`, `umbral=0.69`  
**Valor nuevo:** `k=2`, `umbral=0.65`  
**Fecha del cambio:** 2026-11-09  
**Justificación:** La calibración con `k=2` y `umbral=0.65` cumple el piso de cobertura total >= 70% y cobertura de integración >= 50%. La abstención correcta (53.85%) no alcanza el piso de 70%. El cambio fue aprobado por docente-colegio-1 y docente-colegio-2 en `data/aprobacion_umbrales_20261109.json`.

La abstención de 53.85% corresponde solo a la calibración complementaria de 60 consultas. La evaluación final independiente CP07 del 2026-11-16 registró 15/15 abstenciones correctas y 15/15 consultas adversariales bloqueadas; véase `docs/evidencias/pi13/rag_eval_cp04_cp07_20261116.json`.

## D-02: Muestras y campanas de usuarios

La planificacion PI13/tesis de 14 estudiantes y 2 docentes es distinta del piloto historico v1.0 de 10 personas. Se separan tres registros que antes aparecian mezclados:

- El protocolo historico v1.0, `protocolo-baseline-20261109.md`, describe una muestra prevista de 10 personas (5 docentes y 5 estudiantes). El registro de ejecucion asociado declara 10 personas, pero con roles 6 docentes y 4 estudiantes; se conserva esa discrepancia como historica.
- La campana de aceptacion PI13 del 2026-11-09 reporta n=10 (6 docentes y 4 estudiantes) en `data/sus_scores.json` y `data/paired_time_summary.json`. Ese resultado no corresponde a S-01.
- S-01, fechada 2026-11-06, registra 16 personas (14 estudiantes y 2 docentes) en `data/usuarios/sesiones.csv`. Su protocolo descriptivo separado es `protocolo-sesion-S-01-v2.0.md`.

Los analisis de cada campana se mantienen separados. Para S-01, la cantidad total declarada no sustituye el n verificable de cada instrumento: las respuestas SUS fueron cotejadas con los cuestionarios originales, que permanecen bajo custodia; las observaciones y tiempos individuales tambien se conservan bajo custodia y no se distribuyen en el repositorio. Solo se publican resultados agregados.

## D-03: Criterio p95 de carga (CP08)

**PI12:** p95 ≤ 2 s  
**Tesis y acceptance_thresholds.json:** p95 ≤ 800 ms  
**Justificación:** El umbral de 800 ms aparece en `data/acceptance_thresholds.json` como criterio transaccional. El acta `data/aprobacion_umbrales_20261109.json` aprueba umbrales de OE2 y RNF-08, pero no establece explícitamente la aprobación del límite transaccional de 800 ms. El resultado observado de 785,40 ms satisface ambos criterios (800 ms y 2 s), pero falta constancia expresa de cuándo se decidió el criterio de 800 ms. El valor de 2 s de PI12 era una referencia preliminar.

## D-04: Banco de evaluación final

**Banco de evaluación:** `data/rag_validation_100.json` (N=100). La evaluación final CP07 del 2026-11-16 registra los 100 registros.

## D-05: RNF-02 p95 no logrado

**Planificado:** p95 <= 5000 ms  
**Observado:** 55732.48 ms  
**Justificación:** El p95 excede el umbral por consultas factuales con generación larga. La mediana cumple <= 3000 ms. Se requiere una nueva ejecución optimizada para reducir la cola de latencia.

## D-06: Conciliación de códigos PI11–PI12 y PI13

El registro previo de PI13 reutilizaba CP02, CP03, CP06, CP07, CP09 y CP12 con significados diferentes al plan. Se conservan CP01–CP12 según la tabla 2.3 del Word PI11–PI12; las pruebas adicionales reciben CP13–CP24. `correspondencia-casos.csv` documenta separaciones y equivalencias; `historico/` conserva los CSV anteriores.

La conciliación separa ejecución de aceptación y explicita los casos sin ficha individual. No cambia mediciones, metas ni fechas históricas y no equivale a repetir la campaña. Las referencias de calibración se distinguen del caso de evaluación final CP07.
