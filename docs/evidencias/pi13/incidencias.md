# Incidencias — PI13

| ID | Fecha | Caso | Descripción | Severidad | Acción | Estado |
|----|-------|------|-------------|-----------|--------|--------|
| I-01 | 2026-11-01 | PostgreSQL temp-permission | Previo `PermissionError` en directorio temp de Windows al ejecutar pytest con PostgreSQL; no afecta a las pruebas unitarias con SQLite. | Media | Usar SQLite para pruebas unitarias, PostgreSQL solo para validación de integración controlada. | Cerrada |
| I-02 | 2026-11-09 | Lighthouse no ejecutado | No existe script ni reporte de Lighthouse en el repo para RNF-05 (accesibilidad >= 90). | Alta | Crear `scripts/lighthouse/lighthouse_run.js` y reporte en `docs/evidencias/pi13/lighthouse/`. | Abierta |
| I-03 | 2026-11-01 | Corrida k6 inicial fallida | Corrida con pool 5+10 falló al 50 VU (100% errores, p95 54,551.60 ms). | Alta | Ajustar pool a 30/30 y repetir; ambos perfiles cumplen umbrales. | Cerrada |
| I-04 | 2026-11-01 | HTTP 404 de gemini-2.5 | El modelo `gemini-2.5` no disponible; se usa `gemini-3.6-flash` como solicitado. | Baja | Documentar modelo efectivo en manifiesto y ENTORNO.md. | Cerrada |
| I-05 | 2026-11-09 | UCI de expertos insatisfactoria | ICC = -0.2308 (insuficiente parcial) en rúbrica de fidelidad. | Media | Mantener resultado real sin forzar umbrales; registrar como hallazgo. | Abierta |
