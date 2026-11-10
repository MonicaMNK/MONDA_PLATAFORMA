# Resultado funcional por módulo — PI13

Casos ejecutados: 13 (CP01–CP11, CP12a, CP12b)  
Casos aprobados: 13  
Casos no logrados: 0  
Casos pendiente: 0  
% de éxito global: 100%

## Por módulo

| Módulo | Casos | Aprobados | No logrados | Pendiente | % éxito |
|--------|-------|-----------|-------------|-----------|---------|
| M1 - Control de acceso y autenticación | CP04, CP10 | 2 | 0 | 0 | 100% |
| M2 - Indexación y contenido | CP01 | 1 | 0 | 0 | 100% |
| M3 - Consulta RAG con citas | CP02, CP09 | 2 | 0 | 0 | 100% |
| M4 - Generación y publicación de evaluaciones | CP02 | 1 | 0 | 0 | 100% |
| M5 - Sincronización offline | CP07 | 1 | 0 | 0 | 100% |
| M6 - Analítica y alertas (OE3) | CP05, CP06 | 2 | 0 | 0 | 100% |
| M7 - Carga y rendimiento (RNF-01) | CP08 | 1 | 0 | 0 | 100% |
| M8 - Calidad y estándares (RNF-04/05/06/07/08) | CP12a, CP12b | 2 | 0 | 0 | 100% |

## Fuente de los resultados

- 78 pruebas de backend aprobadas (suite SQLite)
- k6: 25 VU p95=739.61 ms, 50 VU p95=785.40 ms, errores 0%, degradación 6.19% (RNF-01 cumple)
- RAG calibración (banco rag_calibration_integration_20261109.json, 60 consultas): cobertura factual 85.00%, integración 66.67%, abstención correcta 75.00%, adversariales 75.00%, precisión de citas 82.61%
- RAG latencia (banco rag_validation_100.json, 85 consultas): mediana 1396.55 ms (cumple <= 3000 ms), p95 4850.00 ms (cumple <= 5000 ms)
- SUS: 86.25 (cumple >= 68); mediana global 87.5; docentes 87.5; estudiantes 84.38
- Cronbach alpha: general 0.939, docentes 0.8711, estudiantes 0.9803
- Tiempos pareados: speedup 3.92x (manual 185.49 s vs Monda 47.33 s); ahorro medio 138.16 s
- Disponibilidad: 99.72% (cumple >= 99.5%)
- Lighthouse accesibilidad: 92 (cumple >= 90)
