# Perfil k6 para RNF-01

`k6_monda_load.js` mide rutas transaccionales de lectura con datos existentes: analítica, listado de materiales y exportación autorizada. No envía preguntas ni materiales a Gemini.

Los umbrales de carga y de la campaña RAG viven en `data/acceptance_thresholds.json`; k6, el comparador de corridas y el evaluador Gemini leen esa fuente.

El perfil ejecuta cinco minutos de calentamiento y quince minutos de medición. En la medición aplica p95 < 800 ms y tasa de fallos < 1 %. Ejecuta primero la comparación con 25 VU y luego con 50 VU para calcular la degradación; registra recursos de CPU, memoria y red del servidor por separado.

En PowerShell, define `LOAD_BASE_URL`, `LOAD_COURSE_ID` y `LOAD_BEARER_TOKEN` con una cuenta de carga autorizada. El token dura 30 minutos, suficiente para un perfil de veinte minutos. Guarda cada salida JSON en una ruta distinta:

```powershell
$null = New-Item -ItemType Directory -Force artifacts
$env:LOAD_USERS = "25"
$env:K6_SUMMARY_PATH = "artifacts/load-25.json"
k6 run scripts/k6_monda_load.js

$env:LOAD_USERS = "50"
$env:K6_SUMMARY_PATH = "artifacts/load-50.json"
k6 run scripts/k6_monda_load.js

python scripts/compare_k6_summaries.py artifacts/load-25.json artifacts/load-50.json --output artifacts/comparison.json
```

Si k6 no está instalado en Windows, usa la imagen oficial desde Docker. Mantén las variables de entorno definidas en la sesión de PowerShell y sustituye cada `k6 run` por:

```powershell
$repo = (Get-Location).Path
docker run --rm --mount "type=bind,source=$repo,target=/work" -w /work `
  --env LOAD_BASE_URL --env LOAD_COURSE_ID --env LOAD_BEARER_TOKEN `
  --env LOAD_USERS --env K6_SUMMARY_PATH `
  grafana/k6:2.3.0 run scripts/k6_monda_load.js
```

Repite ambos perfiles sobre el mismo commit, base y equipo. Los resultados locales describen ese entorno y no acreditan disponibilidad mensual ni el desempeño de AWS. No guardes tokens en los artefactos.
