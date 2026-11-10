# Incidencias — PI13

| ID | Fecha | Caso | Descripción | Severidad | Acción | Estado |
|----|-------|------|-------------|-----------|--------|--------|
| I-01 | 2026-11-01 | PostgreSQL temp-permission | Previo `PermissionError` en directorio temp de Windows al ejecutar pytest con PostgreSQL; no afecta a las pruebas unitarias con SQLite. | Media | Usar SQLite para pruebas unitarias, PostgreSQL solo para validación de integración controlada. | Cerrada |
| I-02 | 2026-11-09 | Lighthouse reporte incompleto | Script `scripts/lighthouse/lighthouse_run.js` creado; reporte JSON con score 92 pero sin salida original completa (solo 12 de 28 auditorías, sin HTML, sin metadatos de ejecución). | Alta | Regenerar reporte Lighthouse con salida completa y verificar URL de la interfaz. | Abierta |
| I-03 | 2026-11-01 | Corrida k6 inicial fallida | Corrida con pool 5+10 falló al 50 VU (100% errores, p95 54,551.60 ms). | Alta | Ajustar pool a 30/30 y repetir; ambos perfiles cumplen umbrales. | Cerrada |
| I-04 | 2026-11-01 | HTTP 404 de gemini-2.5 | El modelo `gemini-2.5` no disponible; se usa `gemini-3.6-flash` como solicitado. | Baja | Documentar modelo efectivo en manifiesto y ENTORNO.md. | Cerrada |
| I-05 | 2026-11-09 | ICC de expertos insuficiente | ICC(2,1) = -0.2308 (concordancia insuficiente). El CSV original `data/expert_ratings_20261109.csv` no cambió; el valor 0.85 no es reproducible desde los datos fuente. | Media | Requere segunda valoración con nuevo archivo de calificaciones y su propio cálculo de ICC. | Abierta |
