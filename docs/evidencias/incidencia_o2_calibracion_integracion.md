# Incidencia O2 — Calibración sin preguntas de integración

## Estado del problema

La calibración actual (`data/rag_calibration_gemini_abstencion_20261101.json`) usa 100 consultas (80 respondibles, 20 controles) pero **no las clasifica por categoría** (factual / integración / sin evidencia / adversarial). La estratificación de validación cruzada usa solo `(curso, condición respondible, PDF esperado)`, sin incluir categoría de pregunta. La función de selección maximiza la abstención correcta sujeta a cobertura mínima, sin medir si el sistema puede integrar evidencia de varios fragmentos.

Con `k=1`, el RAG entrega al generador un único fragmento. Si una pregunta de integración requiere dos o más fragmentos, el segundo no llega al contexto y el modelo debe omitir parte de la respuesta o inferirla. Por lo tanto, `k=1` y umbral 0,69 son una configuración inicial para recuperación simple, **no una calibración validada para integración**.

La evaluación live original muestra evidencia diagnóstica (no probatoria): se generaron respuestas para 20 de las 30 consultas de integración; 17 de esas 20 fueron correctas (85 % de las respondidas), pero solo 17/30 = 56,7 % sobre todo el grupo de integración. Esto demuestra una brecha con `k=1, 0,69` pero no demuestra que la calibración estuviera optimizada para integración.

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

## Procedimiento de calibración (para ejecutar)

1. **Revisión docente del banco**: un docente revisa y aprueba las 60 consultas de `rag_calibration_integration_20261109.json`, confirmando que `required_fragments`, `gold_answer` y `integration_relationships` son correctos. Cambiar `status` de `pending_teacher_review` a `approved`.

2. **Ejecutar calibración**: correr `scripts/calibrate_rag_gemini.py` con el nuevo banco. El script:
   - Vectoriza fragmentos y consultas con Gemini embedding-2
   - Ejecuta validación cruzada de 5 pliegues estratificada por categoría
   - Evalúa combinaciones de k ∈ {1, 2, 3, 4, 5, 6, 8}, umbral ∈ {0.20–0.80 paso 0.02}, margen ∈ {0.0, 0.02, 0.05, 0.10, 0.15}
   - Selecciona la configuración que maximiza abstención correcta sujeta a: cobertura total ≥ 70 % Y cobertura de integración ≥ 50 %

3. **Seleccionar configuración final**: la configuración elegida (k, umbral, margen) se fija y se registra con el commit del código. No se ajusta mirando el banco final de evaluación.

4. **Evaluación final live independiente**: ejecutar sobre un banco congelado que **no** se usó para calibrar (p. ej., `rag_validation_100.json`), reportando por separado:
   - Cobertura factual y cobertura de integración
   - Recall@k de fragmentos requeridos para integración
   - Corrección y fidelidad de respuestas integradas
   - Validez y completitud de citas
   - Respuestas indebidas a controles y abstenciones incorrectas

## Criterio de cierre de la incidencia

La incidencia O2 queda cerrada cuando se cumplan **los tres** requisitos:

| Requisito | Estado | Evidencia |
|-----------|--------|-----------|
| Calibración reproducible que incluya casos de integración | Cumplido | `data/rag_calibration_integration_20261109.json` (banco con 60 consultas, 27 de integración); `scripts/calibrate_rag_gemini.py` actualizado con métricas de integración y opción `--fixture`; `data/rag_calibration_integration_results_20261109.json` (resultados con k=2, threshold=0.65, margin=0.0, cobertura total 74.47%, cobertura integración 66.67%) |
| Configuración seleccionada con métricas de integración | Cumplido | Resultados documentan k=2 seleccionado por cumplir ambos pisos (cobertura total 74.47% >= 70%, cobertura integración 66.67% >= 50%); k=1 excluido por integración 37.04% < 50% |
| Evaluación live sobre datos independientes que confirme la configuración | Pendiente | Debe ejecutarse sobre banco congelado independiente (`rag_validation_100.json`, ahora 85 preguntas tras eliminar 15 duplicados con el banco de calibración) con k=2, threshold=0.65, margin=0.0; los resultados de calibración recomiendan este paso como siguiente acción |

La incidencia O2 queda parcialmente cerrada: los requisitos 1 y 2 están cumplidos (calibración con integración y configuración seleccionada con métricas de integración). El requisito 3 (evaluación live independiente sobre datos no usados en calibración) permanece pendiente y es el siguiente paso para dar por cerrada la incidencia definitivamente. La configuración k=2, threshold=0.65, margin=0.0 está aplicada en el runtime (`backend/app/core/config.py`, defaults RAG_TOP_K=2, RAG_SIMILARITY_THRESHOLD=0.65). El banco de calibración anterior (`rag_calibration_gemini_abstencion_20261101.json`) se conserva como antecedente con su alcance declarado (sin categorías de integración).

## Archivos relacionados

- `data/rag_calibration_integration_20261109.json` — Nuevo banco de calibración con categorías (approved, revisado por docente-colegio-1)
- `scripts/calibrate_rag_gemini.py` — Script actualizado con métricas de integración y estratificación por categoría
- `data/rag_calibration_gemini_abstencion_20261101.json` — Calibración previa (antecedente, sin integración)
- `data/rag_validation_100.json` — Banco final de evaluación (40 factual, 30 integración, 15 sin_evidencia, 15 adversarial); no usar para calibración
- `data/validation_manifest.json` — Hashes de todos los artefactos
