# Resultado de carga k6 local — 9 de noviembre de 2026

Se usó k6 v2.3.0 (imagen `grafana/k6`) contra la app Monda local conectada a PostgreSQL/pgvector. Cada perfil ejecutó cinco minutos de calentamiento y quince de medición sobre analítica, listado de materiales y exportación CSV. El curso y la cuenta fueron datos sintéticos; no se usaron datos de estudiantes. La aceptación de términos de la cuenta está marcada como fixture simulado.

## Corrida inicial con pool predeterminado (5 conexiones + 10 overflow)

| Perfil | p95 en medición | Solicitudes fallidas | Fallas de aceptación | Resultado |
|---|---:|---:|---:|---|
| 25 VU (referencia) | 807.96 ms | 0.0431 % | 0.0431 % | Falla p95 < 800 ms |
| 50 VU (objetivo) | 54,551.60 ms | 100 % | 100 % | Falla p95 < 800 ms y errores < 1 % |

El comparador calcula **6,651.76 % de degradación** del p95 entre 25 y 50 VU, frente al máximo de 20 %. En los logs de la app se observó agotamiento del pool SQLAlchemy (`QueuePool`: 5 conexiones + 10 overflow) y timeouts de solicitudes. Las tres rutas respondieron HTTP 200 en el preflight de una petición; la app no sostuvo la misma carga concurrente.

Los resultados describen esta máquina local; no acreditan desempeño de producción ni de AWS. Los datos fuente están en [k6 25 VU](k6-25-vu-2026-11-09.json), [k6 50 VU](k6-50-vu-2026-11-09.json) y [comparación](k6-comparison-2026-11-09.json).

## Repetición con pool PostgreSQL 30/30

Se configuró `DB_POOL_SIZE=30` y `DB_MAX_OVERFLOW=30` en la aplicación y en Docker Compose. El ajuste se aplica solo a PostgreSQL; SQLite conserva su comportamiento anterior. Se repitieron los perfiles de cinco minutos de calentamiento y quince minutos de medición sobre la misma aplicación local, curso sintético y rutas.

Después del cambio, la suite local con SQLite aprobó **78 pruebas, 0 fallidas y 1 advertencia** en 145.35 s. También se verificó dentro del contenedor PostgreSQL que SQLAlchemy arrancó con `pool_size=30` y `max_overflow=30`.

| Perfil | p95 en medición | Solicitudes fallidas | Fallas de aceptación | Resultado |
|---|---:|---:|---:|---|
| 25 VU (referencia) | 739.61 ms | 0 % | 0 % | Cumple p95 < 800 ms y errores < 1 % |
| 50 VU (objetivo) | 785.40 ms | 0 % | 0 % | Cumple p95 < 800 ms y errores < 1 % |

El comparador calcula **6.19 % de degradación** entre 25 y 50 VU, por debajo del máximo de 20 %. En el perfil de 50 VU, el p95 fue 785.40 ms, con 0 % de solicitudes fallidas y 0 % de fallas de aceptación; cumple los umbrales configurados. La comparación reproducida desde los JSON crudos quedó `passed: true`. No se modificaron los umbrales.

Los artefactos de esta repetición están en [k6 25 VU con pool 30/30](k6-25-vu-pool-30-30-2026-11-09.json), [k6 50 VU con pool 30/30](k6-50-vu-pool-30-30-2026-11-09.json) y [comparación 30/30](k6-comparison-pool-30-30-2026-11-09.json).
