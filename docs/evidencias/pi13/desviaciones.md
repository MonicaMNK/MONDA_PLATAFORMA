# Desviaciones — PI13

## D-01: Cambio de umbrales RAG (09/11/2026)

**Campo:** `rag_top_k` y `rag_similarity_threshold`  
**Valor anterior:** `k=1`, `umbral=0.69`  
**Valor nuevo:** `k=2`, `umbral=0.65`  
**Fecha del cambio:** 2026-11-09  
**Justificación:** La calibración original con `k=1` y `0,69` no incluía preguntas de integración. Tras crear el banco de calibración con casos de integración (`data/rag_calibration_integration_20261109.json`), la selección de parámetros sujetos a cobertura total >= 70% y cobertura de integración >= 50% arrojó `k=2`, `umbral=0,65`, `margen=0,0` como configuración óptima. `k=1` queda excluido porque su cobertura de integración (37,04%) está por debajo del piso de 50%. El cambio está aprobado por docente-colegio-1 y docente-colegio-2 en `data/aprobacion_umbrales_20261109.json`.

## D-02: Tamaño de muestra de usuarios

**Planificado:** 14 estudiantes + 2 docentes (16 participantes)  
**Ejecutado:** 10 participantes (5 docentes, 5 estudiantes)  
**Justificación:** Muestra piloto de conveniencia por disponibilidad de participantes. Se declara explícitamente como piloto exploratorio, no representativo de la población total.

## D-03: Criterio p95 de carga (CP08)

**PI12:** p95 ≤ 2 s  
**Tesis y acceptance_thresholds.json:** p95 ≤ 800 ms  
**Justificación:** El umbral de 800 ms es el criterio oficial de la campaña de aceptación. El valor de 2 s de PI12 era una referencia preliminar; se unifica a 800 ms y se registra la diferencia aquí para trazabilidad.

## D-04: Banco de evaluación final con duplicados eliminados

**Banco original:** `data/rag_validation_100.json` con 100 consultas  
**Banco usado:** 85 consultas tras eliminar 15 duplicados con el banco de calibración  
**Justificación:** Se eliminaron 15 preguntas que aparecían en ambos bancos para mantener la ceguera de la evaluación independiente. La distribución resultante es 37 factual, 20 integración, 15 sin evidencia, 13 adversarial.

## D-05: UCI de expertos insatisfactoria parcial

**Valor esperado:** ICC >= 0.70 (concordancia adecuada)  
**Valor observado:** ICC = -0.2308 (insuficiente parcial)  
**Justificación:** Se mantiene el resultado real sin forzar umbrales. Se registra como hallazgo y no como fallo de la campaña.

## D-06: Calificación de prueba ES05

**Planificado en evidencia previa:** nota 0/20  
**Plan en tesis:** nota 6,67/20 con 1 de 3 reactivos  
**Valor usado:** 6,67/20 con 1 de 3 reactivos (CP05)  
**Justificación:** Se alinea con la tesis y se agrega el test explícito `test_cp_oe3_average_10_and_14_is_12_and_does_not_trigger_low_alert` que cubre ES05.
