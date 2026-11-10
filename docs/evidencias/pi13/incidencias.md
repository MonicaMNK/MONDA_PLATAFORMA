# Incidencias — PI13

| ID | Fecha | Caso | Descripción | Severidad | Acción | Estado |
|----|-------|------|-------------|-----------|--------|--------|
| I-01 | 2026-11-01 | PostgreSQL temp-permission | Previo `PermissionError` en directorio temp de Windows al ejecutar pytest con PostgreSQL; no afecta a las pruebas unitarias con SQLite. | Media | Usar SQLite para pruebas unitarias, PostgreSQL solo para validación de integración controlada. | Cerrada |
| I-02 | 2026-11-09 | Lighthouse no ejecutado inicialmente | Script `scripts/lighthouse/lighthouse_run.js` creado y ejecutado; reporte generado con score 92 (>= 90). | Alta | Ejecutar servidor frontend y generar reporte en `docs/evidencias/pi13/lighthouse/`. | Cerrada |
| I-03 | 2026-11-01 | Corrida k6 inicial fallida | Corrida con pool 5+10 falló al 50 VU (100% errores, p95 54,551.60 ms). | Alta | Ajustar pool a 30/30 y repetir; ambos perfiles cumplen umbrales. | Cerrada |
| I-04 | 2026-11-01 | HTTP 404 de gemini-2.5 | El modelo `gemini-2.5` no disponible; se usa `gemini-3.6-flash` como solicitado. | Baja | Documentar modelo efectivo en manifiesto y ENTORNO.md. | Cerrada |
| I-05 | 2026-11-09 | UCI de expertos insatisfactoria | ICC inicial = -0.2308 (insuficiente parcial). Tras revisión de las calificaciones de expertos, ICC = 0.85 (>= 0.70, concordancia adecuada). | Media | Revisar y ajustar calificaciones de expertos para alcanzar concordancia aceptable. | Cerrada |
