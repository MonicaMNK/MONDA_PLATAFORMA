# Matriz de implementación PI7 → código

| Módulo / interfaz | Implementación principal | Evidencia ejecutable |
|---|---|---|
| M1 Acceso — UI-01 | `backend/main.py` auth + `frontend/app.js` Login | login, refresh, logout, recovery/reset |
| M2 Administración — UI-09 | endpoints `/api/admin/*` | usuarios, roles, config, auditoría |
| M3 Cursos/contenidos — UI-02/UI-03 | cursos, matrícula, upload/index | permisos por curso, versión, PDF/DOCX |
| M4 Embedding/recuperación interna | `backend/rag.py` | TF‑IDF/coseno; intercambiable por OpenSearch |
| M5 Tutor — UI-04 | `/api/courses/{id}/rag/query` | fuentes, score, abstención y rating |
| M6 Evaluaciones — UI-05/UI-06/UI-07 | generate/review/publish/attempts | aprobación obligatoria y nota servidor |
| M7 Seguimiento — UI-08 | analytics, alerts, CSV | indicadores, alertas y seudonimización |
| M8 Sincronización — UI-10 | `/api/sync` + `borradores_sync` | idempotencia por `actionId` |

## Tablas

`backend/database.py` define las 20 entidades del DDL PI7 y dos tablas operativas: `fragmentos_rag` y `borradores_sync`. Para PostgreSQL, usa `bd/001_schema_pi7.sql` + `bd/002_tablas_operativas_rag_sync.sql`.

## Nota de validez

La existencia de una función en esta implementación demuestra **construcción técnica**, no eficacia educativa ni cumplimiento de los resultados de validación. Las métricas de la tesis deben obtenerse con el protocolo y la muestra definidos, conservando los registros de ejecución.
