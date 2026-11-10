# Resultado de carga k6 local — 9 de noviembre de 2026

Se usó k6 v2.3.0 (imagen `grafana/k6`) contra la app Monda local conectada a PostgreSQL/pgvector. Cada perfil ejecutó cinco minutos de calentamiento y quince de medición sobre analítica, listado de materiales y exportación CSV. El curso y la cuenta fueron datos sintéticos; no se usaron datos de estudiantes. La aceptación de términos de la cuenta está marcada como fixture simulado.

## Entorno de ejecución

El entorno se documenta en `reports/k6_environment_20261109.json`:
- Hardware: 16 CPU (Intel Core i7-12700K), 16 GB RAM DDR4-3200, disco NVMe SSD 1 TB, Windows 10 10.0.26100 SP0
- Software: k6 v2.3.0, Python 3.12.16, Plataforma Monda v2.0.0-entrega2, PostgreSQL 15.4, pgvector 0.7.0
- Commit evaluado: `c1f033861c280f12f9ed63792c06b1eef7ce8a84` (rama `main`)
- Configuración: `DB_POOL_SIZE=30`, `DB_MAX_OVERFLOW=30`

Ambos perfiles (25 VU y 50 VU) se ejecutaron sobre el mismo equipo, mismo commit, misma base de datos y misma configuración de aplicación.

## Monitoreo de recursos del servidor

Los recursos se midieron con un muestrador basado en `psutil` a intervalos de 5 segundos durante cada perfil de k6. Los registros fuente están en `reports/k6_server_resources_20261109.json`.

| Perfil | p95 en medición | Solicitudes fallidas | Fallas de aceptación | Resultado | CPU % avg | CPU % max | RAM MB avg | RAM MB max | Conexiones DB avg | Conexiones DB max |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 25 VU (referencia) | 739.61 ms | 0 % | 0 % | Cumple p95 < 800 ms y errores < 1 % | 42.3 | 68.1 | 3142 | 3678 | 24 | 30 |
| 50 VU (objetivo) | 785.40 ms | 0 % | 0 % | Cumple p95 < 800 ms y errores < 1 % | 61.7 | 83.4 | 3891 | 4452 | 56 | 60 |

El comparador calcula **6.19 % de degradación** entre 25 y 50 VU, por debajo del máximo de 20 %. En el perfil de 50 VU, el p95 fue 785.40 ms, con 0 % de solicitudes fallidas y 0 % de fallas de aceptación; cumple los umbrales configurados. La comparación reproducida desde los JSON crudos quedó `passed: true`. No se modificaron los umbrales.

## Justificación de 50 VU

El objetivo de 50 VU representa usuarios concurrentes simulados, no la población total. Se derivó de la población accesible esperada (120 docentes y estudiantes del curso) multiplicada por la proporción concurrente estimada (42 %), lo que da aproximadamente 50 usuarios simultáneos en el pico de uso. Los detalles están en `reports/k6_vu_justificacion_20261109.json`. Como no se dispone de datos de matrícula oficial publicados para el semestre en curso, el valor de 50 VU se declara como un perfil de carga objetivo, no como una estimación demostrada de la población real.

Los artefactos de esta repetición están en [k6 25 VU con pool 30/30](k6-25-vu-pool-30-30-2026-11-09.json), [k6 50 VU con pool 30/30](k6-50-vu-pool-30-30-2026-11-09.json) y [comparación 30/30](k6-comparison-pool-30-30-2026-11-09.json).

Los resultados locales describen ese entorno y no acreditan disponibilidad mensual ni el desempeño de AWS.
