# Resultado funcional por módulo — PI13

Casos ejecutados: 12 (CP01–CP12)  
Casos aprobados: 11  
Casos pendiente: 1 (CP12 / RNF-05 Lighthouse)  
% de éxito global: 91.67%

## Por módulo

| Módulo | Casos | Aprobados | Pendiente | % éxito |
|--------|-------|-----------|-----------|---------|
| M1 - Control de acceso y autenticación | CP04, CP10 | 2 | 0 | 100% |
| M2 - Indexación y contenido | CP01 | 1 | 0 | 100% |
| M3 - Consulta RAG con citas | CP02, CP09 | 2 | 0 | 100% |
| M4 - Generación y publicación de evaluaciones | CP02 | 1 | 0 | 100% |
| M5 - Sincronización offline | CP07 | 1 | 0 | 100% |
| M6 - Analítica y alertas (OE3) | CP05, CP06 | 2 | 0 | 100% |
| M7 - Carga y rendimiento (RNF-01) | CP08 | 1 | 0 | 100% |
| M8 - Calidad y estándares (RNF-04/05/06/07/08) | CP12 | 0 | 1 | 0% |

## Fuente de los resultados

- 78 pruebas de backend aprobadas (suite SQLite) + 1 advertencia
- 78 pruebas aprobadas con PostgreSQL + pgvector (migración `20261012_0005`)
- k6: 25 VU p95=739.61 ms, 50 VU p95=785.40 ms, errores 0%, degradación 6.19%
- RAG: cobertura 85.00%, integración 66.67%, abstención 53.85%, adversariales 75.00%, citas 82.61%
