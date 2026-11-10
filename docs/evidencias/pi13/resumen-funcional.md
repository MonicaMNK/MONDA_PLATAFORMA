# Resultado funcional por módulo — PI13

Casos ejecutados: 14 (CP01–CP11, CP12a, CP12b, CP12c)  
Casos logrados: 12  
Casos parciales: 1 (CP09 - mediana OK, p95 no logrado)  
Casos no verificados: 1 (CP12a Lighthouse)  
% de éxito global: 85.71% (12/14 logrados)  

Nota adicional: RNF-04 disponibilidad (vinculado a CP08) se declara No verificado al carecer de registro fuente de sondeos individuales.

## Por módulo

| Módulo | Casos | Logrados | Parciales | No verificados | % éxito |
|--------|-------|----------|-----------|----------------|---------|
| M1 - Control de acceso y autenticación | CP04, CP10 | 2 | 0 | 0 | 100% |
| M2 - Indexación y contenido | CP01 | 1 | 0 | 0 | 100% |
| M3 - Consulta RAG con citas | CP02, CP09 | 1 | 1 | 0 | 50% |
| M4 - Generación y publicación de evaluaciones | CP02 | 1 | 0 | 0 | 100% |
| M5 - Sincronización offline | CP07 | 1 | 0 | 0 | 100% |
| M6 - Analítica y alertas (OE3) | CP05, CP06 | 2 | 0 | 0 | 100% |
| M7 - Carga y rendimiento (RNF-01) | CP08 | 1 | 0 | 0 | 100% |
| M8 - Calidad y estándares (RNF-04/05/06/07/08) | CP12a, CP12b, CP12c | 2 | 0 | 1 | 66.67% |

## Fuente de los resultados

- 78 pruebas de backend aprobadas (suite SQLite)
- k6: 25 VU p95=739.61 ms, 50 VU p95=785.40 ms, errores 0%, degradación 6.19% (RNF-01 cumple)
- RAG calibración (banco rag_calibration_integration_20261109.json, 60 consultas): cobertura factual 85.00%, integración 66.67%, abstención correcta 53.85% (NO LOGRADA, < 70%), adversariales 75.00%, precisión de citas 86.17% (81/94, no verificado sin registro recuperable)
- RAG latencia (banco rag_latency_20261109.json, 100 consultas): mediana 1396.55 ms (cumple <= 3000 ms), p95 55732.48 ms (NO CUMPLE <= 5000 ms). RNF-02 parcial.
- SUS: 86.25 (cumple >= 68 media); mediana global 87.5; docentes 87.5; estudiantes 84.38; mínimo 62.5 (no todos >= 68)
- Cronbach alpha: general 0.939, docentes 0.8711, estudiantes 0.9803
- Tiempos pareados: speedup 3.92x (manual 185.49 s vs Monda 47.33 s); ahorro medio 138.16 s; IC 95% [129.577; 146.743]; t(9)=36.4145, p=4.40e-11, d_z=11.5153
- Disponibilidad: 99.72% reportada en resumen, pero sin registro fuente verificable → No verificado
- Lighthouse accesibilidad: reporte con score 92 pero sin salida original completa → No verificado
