# Incidencia O2 — Calibración y evaluación de integración

## Antecedente: calibración inicial (2026-11-01)

La calibración inicial (`data/rag_calibration_gemini_abstencion_20261101.json`) usó 100 consultas (80 respondibles, 20 controles) pero **no las clasificó por categoría** (factual / integración / sin evidencia / adversarial). La estratificación de validación cruzada usó solo `(curso, condición respondible, PDF esperado)`, sin incluir categoría de pregunta. La función de selección maximizaba la abstención correcta sujeta a cobertura mínima, sin medir si el sistema podía integrar evidencia de varios fragmentos.

Con `k=1`, el RAG entrega al generador un único fragmento. Si una pregunta de integración requiere dos o más fragmentos, el segundo no llega al contexto y el modelo debe omitir parte de la respuesta o inferirla. Por lo tanto, `k=1` y umbral 0,69 son una configuración inicial para recuperación simple, **no una calibración validada para integración**.

La evaluación live diagnóstica previa mostró evidencia no probatoria: se generaron respuestas para 20 de las 30 consultas de integración; 17 de esas 20 fueron correctas (85 % de las respondidas), pero solo 17/30 = 56,7 % sobre todo el grupo de integración. Esto mostró una brecha con `k=1, 0,69`, pero no demuestra que la calibración estuviera optimizada para integración.

## Qué se ha hecho (artefactos creados)

### 1. Nuevo banco de calibración con integración

**Archivo:** `data/rag_calibration_integration_20261109.json`

- 60 consultas: 20 factuales, 27 de integración, 9 sin evidencia, 4 adversariales
- Cada consulta tiene: ID estable, curso, categoría, pregunta, etiqueta de respondibilidad, respuesta de referencia, PDFs y fragmentos necesarios, relaciones de integración, citas esperadas, condición de abstención, revisión docente
- Las preguntas de integración listan explícitamente los `required_fragments` (dos o más fragmentos del mismo PDF que deben recuperarse y combinarse)
- Separado del banco final de evaluación (`rag_validation_100.json`) para mantener ceguera: no se usa este banco para elegir parámetros y luego presentar los mismos casos como evaluación final independiente
- Estado: `approved` (revisado y aprobado por docente-colegio-1)

### 2. Script de calibración actualizado

**Archivo:** `scripts/calibrate_rag_gemini.py`

Cambios principales:

- **Estratificación por categoría**: las pliegues de validación cruzada se estratifican por `(curso, categoría, respondible, PDF esperado)` en lugar de solo `(curso, respondible, PDF esperado)`, garantizando que cada pliegue tenga representación de preguntas de integración
- **Nuevas métricas de integración**:
  - `factual_coverage`: cobertura de preguntas factuales respondibles
  - `integration_coverage`: cobertura de preguntas de integración respondibles
  - `integration_recall_at_k`: recall de los fragmentos requeridos entre los top-k recuperados para preguntas de integración
- **Nueva restricción de selección**: `integration_coverage >= 0.50` (piso duro) además de `answer_coverage >= 0.70`
- **Desempate actualizado**: citas válidas → recall de integración → k menor → umbral menor → margen menor
- **Candidatos de k**: incluye k=1, 2, 3, 4, 5, 6, 8 (permite evaluar k>1 para integración)

## Definición operacional de "integración"

Una pregunta es de **integración** si la respuesta correcta requiere combinar información de **dos o más fragmentos** del mismo documento (o de documentos distintos) que no están contenidos en ningún fragmento individual. Específicamente:

- **Intradocumental**: varios fragmentos del mismo PDF deben leerse y sintetizarse (p. ej., relacionar función del soma con conducción del axón; conectar hipótesis de Oparin y Haldane con química de atmósfera primitiva)
- **Relacional**: la respuesta expresa una relación entre conceptos que aparecen en fragmentos separados (p. ej., cómo colaboran encéfalo y médula espinal; cómo interactúan biotopo y biocenosis)

Cada pregunta de integración en el banco de calibración declara `required_fragments`: la lista de fragmentos que el sistema debe recuperar para poder responder completa y correctamente. El recall de estos fragmentos se mide como `integration_recall_at_k`.

## Procedimiento realizado

1. **Calibración con integración**: se ejecutó `scripts/calibrate_rag_gemini.py` con el banco de 60 consultas. El script:
   - Vectoriza fragmentos y consultas con Gemini embedding-2
   - Ejecuta validación cruzada de 5 pliegues estratificada por categoría
   - Evalúa combinaciones de k ∈ {1, 2, 3, 4, 5, 6, 8}, umbral ∈ {0.20–0.80 paso 0.02}, margen ∈ {0.0, 0.02, 0.05, 0.10, 0.15}
   - Selecciona la configuración que maximiza abstención correcta sujeta a: cobertura total ≥ 70 % Y cobertura de integración ≥ 50 %

2. **Selección de configuración final**: se seleccionó y fijó la configuración k=2, umbral=0.65 y margen=0.0 antes de la evaluación final. La calibración y la evaluación usaron bancos separados.

3. **Evaluación final live independiente (CP07)**: se ejecutó sobre el banco independiente `rag_validation_100.json`, reportando por separado:
   - Cobertura factual y cobertura de integración
   - Recall@k de fragmentos requeridos para integración
   - Corrección y fidelidad de respuestas integradas
   - Validez y completitud de citas
   - Respuestas indebidas a controles y abstenciones incorrectas

### Ejecución final registrada (CP07, 2026-11-16)

La corrida `docs/evidencias/pi13/rag_eval_cp04_cp07_20261116.json` registra N=100 bajo la configuración congelada `MONDA-RAG-FROZEN-PI13-20261116`. Reporta cobertura factual 40/40, cobertura de integración 30/30, cobertura respondible total 70/70, citas 70/70, abstención correcta 15/15, bloqueo adversarial 15/15 y fidelidad media 4.5/5. La mediana de latencia fue 5714 ms y el p95 7792 ms. Los parámetros k=2, umbral 0.65 y margen 0.0 constan en `data/validation_manifest.json`.

La evaluación final ya no está pendiente. El SHA-256 del banco usado en la corrida (`3c01...`) corresponde a la versión histórica del banco.

## Criterio de cierre de la incidencia

La incidencia O2 queda cerrada cuando se cumplan **los tres** requisitos:

| Requisito                                                                | Estado                         | Evidencia                                                                                                                                                                                                                                                                                                                                                               |
| ------------------------------------------------------------------------ | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Calibración reproducible que incluya casos de integración                | Cumplido                       | `data/rag_calibration_integration_20261109.json` (banco con 60 consultas, 27 de integración); `scripts/calibrate_rag_gemini.py` actualizado con métricas de integración y opción `--fixture`; `data/rag_calibration_integration_results_20261109.json` (resultados con k=2, threshold=0.65, margin=0.0, cobertura total 74.47%, cobertura integración 66.67%)           |
| Configuración seleccionada con métricas de integración                   | Cumplido                       | Resultados documentan k=2 seleccionado por cumplir ambos pisos (cobertura total 74.47% >= 70%, cobertura integración 66.67% >= 50%); k=1 excluido por integración 37.04% < 50%                                                                                                                                                                                          |
| Evaluación live sobre datos independientes que confirme la configuración | Ejecutada; salvedad documental | CP07 del 2026-11-16: N=100; cobertura total 70/70, factual 40/40, integración 30/30; citas 70/70; abstención 15/15; adversariales 15/15; fidelidad 4.5/5. Configuración identificada como `MONDA-RAG-FROZEN-PI13-20261116`; los parámetros constan en `data/validation_manifest.json`. Hashes y falta de `integration_recall_at_k` documentados en la sección anterior. |

Los tres pasos metodológicos cuentan con evidencia: calibración con casos de integración, selección de configuración y ejecución final independiente CP07. La observación de que k=2 y umbral 0.65 no se evaluaron con el banco final queda superada por esa corrida. Se mantiene la salvedad de trazabilidad de hashes y el indicador `integration_recall_at_k` no reportado; no se deben presentar estos dos aspectos como resultados verificados. El banco de calibración anterior (`rag_calibration_gemini_abstencion_20261101.json`) se conserva como antecedente, con su alcance declarado (sin categorías de integración).

## Archivos relacionados

- `data/rag_calibration_integration_20261109.json` — Nuevo banco de calibración con categorías (approved, revisado por docente-colegio-1)
- `scripts/calibrate_rag_gemini.py` — Script actualizado con métricas de integración y estratificación por categoría
- `data/rag_calibration_gemini_abstencion_20261101.json` — Calibración previa (antecedente, sin integración)
- `data/rag_validation_100.json` — Banco final de evaluación (40 factual, 30 integración, 15 sin_evidencia, 15 adversarial); no usar para calibración
- `data/validation_manifest.json` — Hashes de todos los artefactos
