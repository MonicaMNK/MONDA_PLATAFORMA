# Perfil k6 para RNF-01

`k6_monda_load.js` mide rutas transaccionales de lectura con datos existentes: analítica, listado de materiales y exportación autorizada. No envía preguntas ni materiales a Gemini.

El perfil ejecuta cinco minutos de calentamiento y quince minutos de medición. En la medición aplica p95 < 800 ms y tasa de fallos < 1 %. Ejecuta primero la comparación con 25 VU y luego con 50 VU para calcular la degradación; registra recursos de CPU, memoria y red del servidor por separado.

En PowerShell, define `LOAD_BASE_URL`, `LOAD_COURSE_ID` y `LOAD_BEARER_TOKEN` con una cuenta de carga autorizada. El token dura 30 minutos, suficiente para un perfil de veinte minutos. Guarda cada salida JSON en una ruta distinta:

```powershell
$env:LOAD_USERS = "25"
$env:K6_SUMMARY_PATH = "artifacts/load-25.json"
k6 run scripts/k6_monda_load.js

$env:LOAD_USERS = "50"
$env:K6_SUMMARY_PATH = "artifacts/load-50.json"
k6 run scripts/k6_monda_load.js
```

Repite ambos perfiles sobre el mismo commit, base y equipo. Los resultados locales describen ese entorno y no acreditan disponibilidad mensual ni el desempeño de AWS. No guardes tokens en los artefactos.
