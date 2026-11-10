# Desviaciones — PI13

## D-01: Cambio de umbrales RAG (09/11/2026)

**Campo:** `rag_top_k` y `rag_similarity_threshold`  
**Valor anterior:** `k=1`, `umbral=0.69`  
**Valor nuevo:** `k=2`, `umbral=0.65`  
**Fecha del cambio:** 2026-11-09  
**Justificación:** La calibración con `k=2` y `umbral=0.65` cumple ambos pisos: cobertura total >= 70% y cobertura de integración >= 50%. La selección de parámetros arrojó esta configuración como óptima. El cambio fue aprobado por docente-colegio-1 y docente-colegio-2 en `data/aprobacion_umbrales_20261109.json`.

## D-02: Tamaño de muestra de usuarios

**Planificado:** 14 estudiantes + 2 docentes (16 participantes)  
**Ejecutado:** 10 participantes (6 docentes, 4 estudiantes)  
**Justificación:** Muestra piloto de conveniencia por disponibilidad de participantes. Se declara explícitamente como piloto exploratorio, no representativo de la población total. Los CSV fuente (`data/usuarios/sus_respuestas.csv`, `data/usuarios/tiempos_pareados.csv`) contienen 6 filas con rol `docente` y 4 con rol `estudiante`.

## D-03: Criterio p95 de carga (CP08)

**PI12:** p95 ≤ 2 s  
**Tesis y acceptance_thresholds.json:** p95 ≤ 800 ms  
**Justificación:** El umbral de 800 ms es el criterio oficial de la campaña de aceptación, aprobado en `data/aprobacion_umbrales_20261109.json` el 2026-11-09 por docente-colegio-1 y docente-colegio-2. El valor de 2 s de PI12 era una referencia preliminar; se unifica a 800 ms para trazabilidad.

## D-04: Banco de evaluación final con duplicados eliminados

**Banco original:** `data/rag_validation_100.json` con 100 consultas  
**Banco usado:** 85 consultas tras eliminar 15 duplicados con el banco de calibración  
**Justificación:** Se eliminaron 15 preguntas que aparecían en ambos bancos para mantener la ceguera de la evaluación independiente. La distribución resultante es 37 factual, 20 integración, 15 sin evidencia, 13 adversarial.
