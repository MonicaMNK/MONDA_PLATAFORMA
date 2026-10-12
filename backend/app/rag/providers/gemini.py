from __future__ import annotations

import math
import requests

from ...core.config import settings
from .base import GenerationResult, RAGProvider


class GeminiProvider(RAGProvider):
    """Gemini REST adapter with a 768-dimension embedding contract for pgvector."""
    name = "gemini"
    embedding_dimensions = 768

    def __init__(self, llm_model: str | None = None, embedding_model: str | None = None):
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY no configurada")
        self.api_key = settings.gemini_api_key
        self.embedding_model = embedding_model or settings.gemini_embedding_model
        self.llm_model = llm_model or settings.gemini_llm_model
        self.base = settings.gemini_base_url.rstrip("/")

    def _post(self, url: str, payload: dict, timeout: int = 30) -> dict:
        response = requests.post(
            url,
            headers={"x-goog-api-key": self.api_key},
            json=payload,
            timeout=timeout,
        )
        if not response.ok:
            # Never include provider response body, which can contain request details.
            raise RuntimeError(f"Gemini HTTP {response.status_code}")
        return response.json()

    @staticmethod
    def _unit_normalize(values: list[float]) -> list[float]:
        norm = math.sqrt(sum(x * x for x in values))
        if not math.isfinite(norm) or norm <= 0:
            raise RuntimeError("Gemini devolvió un embedding nulo o no finito")
        return [x / norm for x in values]

    def embed(self, texts: list[str], task: str = "document") -> list[list[float]]:
        if not texts or any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("Los textos de embedding no pueden estar vacíos")
        out: list[list[float]] = []
        url = f"{self.base}/models/{self.embedding_model}:embedContent"
        for text in texts:
            if self.embedding_model == "gemini-embedding-2":
                # Embedding 2 no admite taskType; la documentación recomienda prefijos
                # textuales coherentes para consulta y documento.
                content_text = (
                    f"task: question answering | query: {text}"
                    if task == "query"
                    else f"title: none | text: {text}"
                )
                payload = {
                    "model": f"models/{self.embedding_model}",
                    "content": {"parts": [{"text": content_text}]},
                    "output_dimensionality": self.embedding_dimensions,
                }
                normalize = False  # Gemini Embedding 2 normaliza dimensiones truncadas.
            else:
                task_type = "RETRIEVAL_QUERY" if task == "query" else "RETRIEVAL_DOCUMENT"
                payload = {
                    "model": f"models/{self.embedding_model}",
                    "content": {"parts": [{"text": text}]},
                    "taskType": task_type,
                    "output_dimensionality": self.embedding_dimensions,
                }
                normalize = True  # Embedding 001 requiere normalización al usar 768 dimensiones.
            data = self._post(url, payload)
            values = data.get("embedding", {}).get("values")
            if not isinstance(values, list):
                raise RuntimeError("Gemini no devolvió embedding")
            vector = [float(value) for value in values]
            if len(vector) != self.embedding_dimensions or any(not math.isfinite(x) for x in vector):
                raise RuntimeError("Gemini devolvió dimensiones o valores de embedding inválidos")
            out.append(self._unit_normalize(vector) if normalize else vector)
        return out

    def generate(self, prompt: str) -> GenerationResult:
        url = f"{self.base}/models/{self.llm_model}:generateContent"
        # Evita parámetros antiguos de muestreo que ya no son aceptados por las
        # generaciones actuales de Gemini 3.x.
        data = self._post(url, {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}, timeout=45)
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini no devolvió candidatos")
        parts = candidates[0].get("content", {}).get("parts") or []
        text = "\n".join(str(part.get("text", "")) for part in parts).strip()
        usage = data.get("usageMetadata") or {}
        return GenerationResult(
            text=text,
            raw=data,
            input_tokens=usage.get("promptTokenCount"),
            output_tokens=usage.get("candidatesTokenCount"),
        )
