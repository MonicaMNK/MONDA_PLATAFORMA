# Resultado funcional por módulo — PI13

Casos ejecutados: 12 (CP01–CP12)  
Casos aprobados: 10  
Casos en revisión: 1 (CP09 / RNF-02 p95 supera umbral)  
Casos pendiente: 1 (CP12 / RNF-05 Lighthouse no ejecutado)  
% de éxito global: 83.33%

## Por módulo

| Módulo | Casos | Aprobados | Revisión | Pendiente | % éxito |
|--------|-------|-----------|----------|-----------|---------|
| M1 - Control de acceso y autenticación | CP04, CP10 | 2 | 0 | 0 | 100% |
| M2 - Indexación y contenido | CP01 | 1 | 0 | 0 | 100% |
| M3 - Consulta RAG con citas | CP02, CP09 | 1 | 1 | 0 | 50% |
| M4 - Generación y publicación de evaluaciones | CP02 | 1 | 0 | 0 | 100% |
| M5 - Sincronización offline | CP07 | 1 | 0 | 0 | 100% |
| M6 - Analítica y alertas (OE3) | CP05, CP06 | 2 | 0 | 0 | 100% |
| M7 - Carga y rendimiento (RNF-01) | CP08 | 1 | 0 | 0 | 100% |
| M8 - Calidad y estándares (RNF-04/05/06/07/08) | CP12 | 0 | 0 | 1 | 0% |

## Fuente de los resultados

- 78 pruebas de backend aprobadas (suite SQLite)
- k6: 25 VU p95=739.61 ms, 50 VU p95=785.40 ms, errores 0%, degradación 6.19% (RNF-01 cumple)
- RAG (calibración out-of-fold, banco rag_calibration_integration_20261109.json): cobertura factual 85.00%, integración 66.67%, abstención correcta 53.85%, adversariales 75.00%, precisión de citas 82.61%
- RAG latencia (banco rag_validation_100.json, 100 consultas): mediana 1396.55 ms (cumple <= 3000 ms), p95 55732.48 ms (SUPERA <= 5000 ms, en revisión)
- SUS: 87.25 (cumple >= 68)
- Tiempos pareados: speedup 3.92x (manual 185.49 s vs Monda 47.33 s)
