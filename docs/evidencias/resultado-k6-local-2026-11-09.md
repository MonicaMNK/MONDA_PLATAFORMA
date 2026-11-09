# Resultado de carga k6 local — 9 de noviembre de 2026

Se usó k6 v2.3.0 (imagen `grafana/k6`) contra la app Monda local conectada a PostgreSQL/pgvector. Cada perfil ejecutó cinco minutos de calentamiento y quince de medición sobre analítica, listado de materiales y exportación CSV. El curso y la cuenta fueron datos sintéticos; no se usaron datos de estudiantes. La aceptación de términos de la cuenta está marcada como fixture simulado.

| Perfil | p95 en medición | Solicitudes fallidas | Fallas de aceptación | Resultado |
|---|---:|---:|---:|---|
| 25 VU (referencia) | 807.96 ms | 0.0431 % | 0.0431 % | Falla p95 < 800 ms |
| 50 VU (objetivo) | 54,551.60 ms | 100 % | 100 % | Falla p95 < 800 ms y errores < 1 % |

El comparador calcula **6,651.76 % de degradación** del p95 entre 25 y 50 VU, frente al máximo de 20 %. En los logs de la app se observó agotamiento del pool SQLAlchemy (`QueuePool`: 5 conexiones + 10 overflow) y timeouts de solicitudes. Las tres rutas respondieron HTTP 200 en el preflight de una petición; la app no sostuvo la misma carga concurrente.

Los resultados describen esta máquina local; no acreditan desempeño de producción ni de AWS. Los datos fuente están en [k6 25 VU](k6-25-vu-2026-11-09.json), [k6 50 VU](k6-50-vu-2026-11-09.json) y [comparación](k6-comparison-2026-11-09.json).
