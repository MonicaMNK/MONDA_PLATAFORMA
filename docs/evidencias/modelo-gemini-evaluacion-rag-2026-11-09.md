# Modelo efectivo en la evaluación live del RAG

## Identificación

- **Resultado analizado:** [`data/rag_gemini_live_20261101.json`](../../data/rag_gemini_live_20261101.json)
- **Inicio registrado:** 2026-11-09 17:48:13 UTC
- **Fin registrado:** 2026-11-09 19:28:51 UTC
- **Modelo solicitado en el resultado:** `gemini-3.8-flash`
- **Proveedor:** Gemini

## Modelo que respondió

En los 100 resultados individuales, 54 tienen `response_model: gemini-3.6-flash`; los otros 46 no tienen `response_model` porque no registran una generación completada. Por tanto, **las 54 respuestas generadas que conserva el archivo fueron producidas por `gemini-3.6-flash`**.

El resultado registra `gemini-3.8-flash` como modelo solicitado. El código del proveedor permite intentar modelos de respaldo y guarda una advertencia interna cuando usa uno; el evaluador no conserva esa advertencia ni la secuencia de intentos por consulta. La salida es compatible con un respaldo de `gemini-3.8-flash` a `gemini-3.6-flash`, pero este artefacto no permite confirmar el error que originó el cambio.

Esta nota resume los campos ya registrados en el JSON; no representa una nueva ejecución ni modifica el resultado original. Para una ejecución futura, registrar en cada consulta los modelos intentados, el modelo efectivo y el motivo de cada respaldo.
