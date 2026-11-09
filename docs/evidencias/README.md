# Índice de evidencias

Usa los informes fechados más recientes como referencia del estado actual. Los archivos de noviembre 1 conservan resultados de versiones anteriores y se mantienen únicamente para trazabilidad; no describen el estado más reciente.

## Estado actual

| Área                       | Informe principal                                                                          | Resultado registrado                                                                                                                         |
| -------------------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Suite SQLite               | [Resultado del 8 de noviembre](resultado-suite-2026-11-08.md)                              | 78 aprobadas, 0 fallidas, 1 advertencia.                                                                                                     |
| PostgreSQL + pgvector      | [Validación del 9 de noviembre](validacion-postgresql-pgvector-2026-11-09.md)              | Migraciones hasta `20261012_0005` y 78 aprobadas, 0 fallidas, 1 advertencia.                                                                 |
| Recorrido E1–E3 con Gemini | [Evidencia de integración del 9 de noviembre](flujo-e1-e3-postgresql-gemini-2026-11-09.md) | Recorrido por API sobre PostgreSQL local temporal; Gemini real en E1/E2; datos sintéticos en E3. No es una captura de la interfaz.           |
| Evaluación final del RAG   | [Resultado live de Gemini](../../data/rag_gemini_live_20261101.json)                       | 100 consultas; checks métricos con los umbrales revisados y documentados. Pendiente revisión humana de corrección factual.                   |
| Carga k6                   | [Resultado del 9 de noviembre](resultado-k6-local-2026-11-09.md)                           | Repetición con pool 30/30: 25 y 50 VU cumplen los umbrales anotados en el informe. La corrida inicial fallida también permanece documentada. |

## Pendiente de completar

- Revisar manualmente las 70 respuestas de consultas respondibles del resultado live contra `gold_answer` y registrar la conclusión de corrección factual.
- Si la entrega requiere evidencia visual de E2, capturar el recorrido desde la interfaz. La evidencia del 9 de noviembre cubre la API.

## Evidencia histórica

[Resultados del 1 de noviembre](resultado-suite-2026-11-01.md) y demás archivos fechados ese día: registros válidos de aquella fecha, incluidos intentos fallidos, respuestas 503 y recorridos con fallback. No deben usarse para afirmar que el mismo resultado se repitió en la versión actual.
