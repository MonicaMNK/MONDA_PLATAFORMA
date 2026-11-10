# Revisión de evidencias RNF y campaña humana — 9 de noviembre de 2026

## Alcance

Revisión estática de los archivos presentes en el checkout local. No se ejecutaron suites, sondeos, Lighthouse, evaluaciones de Gemini ni sesiones con participantes. Los JSON de campaña declaran resultados; su presencia y coherencia se revisaron por separado de la autenticidad de la ejecución.

## Estado por observación

| Punto | Artefactos encontrados | Resultado de la revisión | Para cerrarlo |
|---|---|---|---|
| Disponibilidad 30 días | `data/acceptance_evidence_rnf.json`; `data/availability_probe_30d_20261109.log` | Log con 2.880 filas de datos cada 15 min, 2.872 HTTP 200 y 8 estados 0, desde 2026-10-10T00:00Z hasta 2026-11-08T23:45Z. Coincide aritméticamente con 99,72 % y 120 min del resumen. Es un archivo local; no hay constancia independiente del sistema que lo produjo durante esos 30 días. | Conservar registros del monitor/runner o una fuente de retención que respalde el origen y continuidad del log. |
| Restauración/RPO/RTO | `docs/DESPLIEGUE_AWS.md` dice que backups y restauración deben probarse. | No se encontró informe ni medición de recuperación. | Registrar backup, entorno, timestamps, integridad de datos, RPO observado y RTO observado, comparados con objetivos. |
| Lighthouse | `reports/lighthouse_20261109.report.json`; resumen RNF. | Existe un resumen con puntajes 92/95/93/100/91, pero no la salida nativa completa de Lighthouse con el conjunto íntegro de auditorías. | Adjuntar el reporte original completo y su configuración/versión/URL/commit. |
| Chrome/Edge/Firefox | `reports/browser_matrix_20261109.csv` | Tiene nueve filas PASS, pero los nueve `evidence_link` apuntan a `datos/evidencias/...` y ninguno de esos archivos existe en esa ruta. Sin capturas/logs no se verifica el resultado visual. | Adjuntar las capturas o trazas reales por navegador y flujo y corregir los enlaces. |
| Cobertura de auditoría | `reports/audit_coverage_20261109.json` | Mide 6 de 10 eventos (60 %) y marca `REVISION_REQUERIDA`. Quedan sin cobertura exportación, cambio de contraseña, cambio de rol y expiración de sesión. Este punto tiene una brecha explícita, no un PASS. | Implementar y probar los cuatro eventos faltantes y repetir la medición. |
| Quality Gate/cobertura crítica | `reports/quality_gate_20261109.json` | Declara PASS con 84,2 % global; sus propios porcentajes críticos son audit 78,5 %, RAG retriever 88,3 %, generator 82,1 % y API eval 76,4 %, frente al mínimo crítico declarado de 85 %. También incluye frontend 71 %. Faltan `reports/coverage.xml` e `reports/htmlcov/index.html`. El PASS contradice los números y el umbral. | Adjuntar salidas originales y resolver la regla del gate. Con mínimo 85 % para esos servicios, los resultados publicados no pasan. |
| SUS | `data/sus_campaign_20261109.json` | Incluye 10 respuestas y puntajes. El recálculo estático reproduce el promedio 86,25 (umbral 68); P007 queda en 62,5. El archivo afirma consentimiento institucional, pero no enlaza el respaldo de autorización ni evidencia de la sesión. La muestra se describe como pequeña y de conveniencia. | Conservar aprobación/consentimiento bajo custodia institucional y trazabilidad del reclutamiento/sesión; presentar el resultado como exploratorio. |
| Expertos, V de Aiken y concordancia | `data/expert_ratings_20261109.csv`; `data/expert_ratings_summary_20261109.json` | Hay 15 calificaciones de 5 ítems por 3 jueces. El resumen declara V de Aiken entre 0,8889 y 1,0, pero ICC(2,1) = -0,2308 indica concordancia muy baja/negativa. El resultado figura PASS sin resolver esa discrepancia. El hash CSV en el resumen es `PLACEHOLDER_EXPERT_CSV_SHA256`, no el hash del archivo. | Recalcular/sustituir hash, revisar concordancia y desacuerdos, especificar criterio de ICC y aportar salida reproducible. No cerrar concordancia como PASS con el valor actual. |
| Mediana/p95 RAG | `data/rag_latency_20261109.json`; `data/rag_gemini_live_20261101.json` | El archivo de latencias tiene 95 filas, no 100; faltan V012, V014, V015, V021 y V029. Sobre esas 95 duraciones, mediana = 1.389,45 ms y p95 = 44.340,12 ms. El resumen declara n=100, mediana 1.392,55 ms y p95 63.578,12 ms. La fecha de creación de latencias (17:00Z) antecede el inicio anotado para la evaluación fuente (17:48Z). 27 duraciones coinciden con la suma embedding+generación (±0,05 ms) y 13 con embedding solamente, aunque se etiquetan como mediciones end-to-end independientes. | Obtener 100 duraciones de extremo a extremo con marcas de inicio/fin de la misma ejecución; corregir el desfase temporal y recalcular global/por categoría. No citar el resumen actual como p95 verificado. |

## Inconsistencias adicionales

- `data/rag_gemini_live_20261109_segunda_evaluacion.json` declara 40 factuales, 30 integración, 15 sin evidencia y 15 adversariales, además de 70 respondibles/30 controles. Sus filas cuentan 40 factuales, 50 integración, 10 sin evidencia, 0 adversariales, 86 respondibles y 14 controles. Aunque declara métricas de 100 %, el desglose no concuerda y no permite validar la evaluación.
- El SHA-256 de `data/paired_time_summary.json` ahora coincide con `data/paired_times_20261109.csv`; se resuelve la discrepancia de hash del resumen pareado. La muestra de 10 pares sigue siendo exploratoria, como advierte el propio archivo.
- `data/aprobacion_umbrales_20261109.json` declara dos aprobadores como `docente-colegio-1/2` a la misma hora, pero no adjunta acta firmada ni mecanismo de aprobación. Los criterios están enumerados; la identidad/aprobación humana no se puede verificar con ese archivo solo.
- `data/validation_manifest.json` contiene hashes coincidentes con los artefactos listados. Sin embargo, declara árbol limpio para `c1f0338`/`develop`; el checkout revisado es `main` y Git muestra `data/...` y `reports/` como archivos locales sin seguimiento. Los hashes fijan contenidos, no prueban que las corridas ocurrieron.

## Por qué no aparecían en `main`

Los reportes y datos de campaña recién encontrados están en el directorio local, pero Git los presenta como no rastreados. Por eso no forman parte del commit actual de `main` ni del remoto. Antes había un JSON de resumen que referenciaba fuentes inexistentes; ahora varias fuentes fueron añadidas localmente, aunque persisten enlaces rotos, faltantes y contradicciones descritas arriba. No se puede concluir solo por su ausencia anterior si las actividades se realizaron fuera del repositorio.

## Estado de cierre

- **Internamente calculable:** disponibilidad 30 días y promedio SUS, con límites de procedencia indicados.
- **Brecha funcional identificada:** auditoría 60 %; cuatro eventos sin cobertura.
- **No aceptable como PASS en su forma actual:** Quality Gate con porcentajes bajo el umbral; concordancia ICC negativa y hash de origen placeholder; segunda evaluación con categorías y denominadores incoherentes.
- **Fuentes o respaldos aún insuficientes:** restauración/RPO/RTO; Lighthouse completo; evidencias visuales de navegador; autorización de participantes; hash/resultado reproducible de expertos; 100 latencias end-to-end consistentes.
- **Integración Git:** los artefactos nuevos siguen fuera del seguimiento de `main`.

