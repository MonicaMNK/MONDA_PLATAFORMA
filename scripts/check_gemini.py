"""Comprueba credenciales y modelos sin imprimir claves ni respuestas privadas."""
from pathlib import Path
import requests
from dotenv import dotenv_values

config = dotenv_values(Path(__file__).resolve().parents[1] / "data" / ".gemini.env")
key = config.get("GEMINI_API_KEY")
if not key:
    raise SystemExit("Falta GEMINI_API_KEY en data/.gemini.env")
response = requests.get("https://generativelanguage.googleapis.com/v1beta/models", headers={"x-goog-api-key": key}, timeout=20)
print(f"Gemini: HTTP {response.status_code}")
if not response.ok:
    error = response.json().get("error", {})
    print("Estado:", error.get("status", "unknown"))
    reasons = [x.get("reason") for x in error.get("details", []) if x.get("reason")]
    print("Motivos:", ", ".join(reasons) or "sin detalle")
    raise SystemExit(1)
for model in response.json().get("models", []):
    if "generateContent" in model.get("supportedGenerationMethods", []) or "embedContent" in model.get("supportedGenerationMethods", []):
        print(model["name"])
