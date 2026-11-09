# Índice de evidencias

Usa los informes fechados más recientes como referencia del estado actual. Los archivos de noviembre 1 conservan resultados de versiones anteriores y se mantienen únicamente para trazabilidad; no describen el estado más reciente.

## Estado actual

| Área | Informe principal | Resultado registrado |
|---|---|---|
| Suite SQLite | [Resultado del 8 de noviembre](resultado-suite-2026-11-08.md) | 78 aprobadas, 0 fallidas, 1 advertencia. |
| PostgreSQL + pgvector | [Validación del 9 de noviembre](validacion-postgresql-pgvector-2026-11-09.md) | Migraciones hasta `20261012_0005` y 78 aprobadas, 0 fallidas, 1 advertencia. |
| Recorrido E1–E3 con Gemini | [Evidencia de integración del 9 de noviembre](flujo-e1-e3-postgresql-gemini-2026-11-09.md) | Recorrido por API sobre PostgreSQL local temporal; Gemini real en E1/E2; datos sintéticos en E3. No es una captura de la interfaz. |
| Carga k6 | [Resultado del 9 de noviembre](resultado-k6-local-2026-11-09.md) | Repetición con pool 30/30: 25 y 50 VU cumplen los umbrales anotados en el informe. La corrida inicial fallida también permanece documentada. |

## Pendiente de completar

- Preparar y revisar con docentes `data/rag_validation_100.json`, con 100 preguntas finales distintas del banco de calibración; ejecutar la evaluación live de Gemini y revisar manualmente respuestas, citas, abstenciones y falsos positivos.
- Si la entrega requiere evidencia visual de E2, capturar el recorrido desde la interfaz. La evidencia del 9 de noviembre cubre la API.

## Evidencia histórica

[Resultados del 1 de noviembre](resultado-suite-2026-11-01.md) y demás archivos fechados ese día: registros válidos de aquella fecha, incluidos intentos fallidos, respuestas 503 y recorridos con fallback. No deben usarse para afirmar que el mismo resultado se repitió en la versión actual.
