# Recorrido E1–E3 con PostgreSQL + pgvector y Gemini — 9 de noviembre de 2026

## Identificación y alcance

- **Commit probado:** `33c08188a7ce877d3c0ae0a709b174c8c442a524`.
- **Entorno:** aplicación local en `http://127.0.0.1:8001`; PostgreSQL 16.15; pgvector 0.8.7.
- **Base temporal aislada:** `monda_e2e_20261109`; migración actual `20261012_0005`.
- **Configuración RAG de esta instancia:** modo `gemini`, modelo `gemini-3-flash-preview`, embeddings `gemini-embedding-2`, `RAG_ALLOW_FALLBACK=0`.
- **Datos:** curso, docente, estudiante y PDF sintéticos. No se usaron datos del colegio ni de estudiantes reales.
- **Procesamiento externo:** el texto del PDF sintético y las preguntas de prueba se enviaron a Gemini. La clave se mantuvo en el entorno temporal del proceso y no se guardó en este informe.

La ejecución se hizo por API HTTP contra una segunda instancia de la aplicación conectada a la base temporal. Es una prueba de integración local, no una prueba de producción ni de AWS.

## E1 — Carga, indexación y aislamiento

| Paso | Resultado |
|---|---|
| Subida de `material-sintetico-e1.pdf` por el docente | HTTP 201 |
| Indexación | Completada; 1 fragmento |
| Proveedor y vector guardado | `gemini` / `gemini-embedding-2`, 768 dimensiones |
| Estudiante sin matrícula intenta consultar el estado del material | HTTP 403 |

El contenido quedó persistido en `monda.fragmentos_rag` dentro de PostgreSQL. El registro del material terminó en estado `indexado`.

## E2 — RAG con Gemini real

Se consultó el curso con dos preguntas; ambas respuestas registran proveedor `gemini` y modelo `gemini-3-flash-preview` en [rag_traces.jsonl](../../data/traces/rag_traces.jsonl).

| Caso | Evidencia observada |
|---|---|
| Pregunta respondible sobre fotosíntesis | Evidencia suficiente; score máximo 0.7816; 1 fuente; respuesta con cita `[F1]`. Latencia total 4,948.47 ms; latencia del proveedor 4,934.02 ms. |
| Pregunta sin respaldo sobre el Mundial de fútbol 2010 | Evidencia insuficiente; score máximo 0.5349, menor que el umbral 0.69; respuesta de abstención. No se generó respuesta factual. Latencia total 1,456.47 ms. |

La consulta sin evidencia recuperó un candidato de baja puntuación, pero el sistema lo rechazó y se abstuvo. No hubo fallback.

## E3 — Evaluación, intento, nota y alerta

- El proveedor registrado en el trabajo de generación fue `gemini`, con 2 reactivos y sin advertencia del proveedor.
- El docente sintético aprobó los 2 reactivos mediante la API y publicó la evaluación.
- El estudiante sintético inició y cerró un intento; se publicaron los resultados.
- La nota fue **0/20** en este escenario intencionalmente sintético.
- La analítica de PostgreSQL registró 1 intento cerrado, promedio 0.0 y alerta abierta `promedio_bajo` con umbral 11/20.

Las respuestas se escogieron para que fueran incorrectas en este fixture y comprobaran la persistencia del resultado y la generación de la alerta. Esto no es una calificación de una persona real ni una evaluación pedagógica de los reactivos.

## Incidencia del ejecutor

El primer bloque de automatización terminó con `KeyError` al construir su resumen, después de completar E1, E2 y crear la matrícula sintética. E3 se reanudó sobre la misma base; el intento de repetir la matrícula devolvió HTTP 409 porque ya existía, y se continuó con esa matrícula. No se repitieron las llamadas E2 ni se duplicó la matrícula.

## Evidencia pendiente para la revisión académica

Este recorrido se hizo por API, no desde el navegador. Por tanto, **no sustituye la captura de E2 en la interfaz** solicitada por la revisión del profesor. También conviene conservar una captura de la configuración de PostgreSQL, la pantalla de respuesta Gemini con `[F1]` y la pantalla de abstención cuando se haga manualmente en la UI.
