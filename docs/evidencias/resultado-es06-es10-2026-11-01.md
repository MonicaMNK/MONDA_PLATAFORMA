# Ejecución local de ES06 y ES10 — 1 de noviembre de 2026

La ejecución usó cuentas y contenido sintéticos, SQLite temporal y el frontend servido por FastAPI. No participaron estudiantes ni docentes del colegio. Estos resultados son evidencia técnica previa a la campaña formal de PI11/PI12; las columnas de resultados futuros de esa campaña permanecen vacías.

| Caso | Procedimiento | Resultado observado | Estado |
|---|---|---|---|
| ES06, publicación sin rol docente | Un docente creó un borrador. Una cuenta estudiante intentó `POST /api/assessments/{id}/publish` con versión y fechas válidas. Se consultó el borrador después. | HTTP 403 `FORBIDDEN`; estado `borrador` y versión sin cambios. | Aprobado en API local. |
| ES10, idempotencia y restricciones de la API | Se envió un `borrador_personal` con `actionId`; se repitió la petición, se cambió el payload con el mismo ID y se intentó sincronizar `assessment_submit`. | `applied`, `repeated`, `conflict` con `IDEMPOTENCY_CONFLICT`, y `rejected` con `OFFLINE_ACTION_NOT_ALLOWED`; persistió un solo borrador y una sola acción para el ID original. | Aprobado en API local. |
| ES10, navegador desconectado | En Chrome se guardó una nota sintética mientras la red estaba desactivada; se recargó la aplicación sin conexión y luego se restableció la red. | La aplicación y el borrador siguieron visibles sin conexión; al reconectar se mostró «1 borrador(es) sincronizados sin duplicados» y cero pendientes. `manifest.webmanifest` y `sw.js` devolvieron HTTP 200. | Aprobado en Chrome local. |

**Archivos:** [pytest ES06/ES10](pytest-es06-es10-2026-11-01.txt), [suite completa](pytest-suite-es06-es10-2026-11-01.txt), [registro del navegador](flujo-es10-browser-2026-11-01.txt), [captura sin conexión](captura-es10-pwa-offline-2026-11-01.png) y [captura tras sincronizar](captura-es10-pwa-sincronizado-2026-11-01.png).

La suite dirigida terminó con **2/2 pruebas aprobadas**. La suite completa, tras marcar como no indexable el PDF sintético del catálogo que requiere OCR, terminó con **27/27 pruebas aprobadas** y una advertencia de deprecación de Starlette. La comprobación visual cubre Chrome en un entorno local temporal. No equivale a una campaña de compatibilidad en otros navegadores o dispositivos, ni cierra D07: los recorridos E1–E3 sobre PostgreSQL + pgvector siguen pendientes.
