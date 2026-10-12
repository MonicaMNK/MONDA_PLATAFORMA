from __future__ import annotations

import requests

from ...core.config import settings
from .base import GenerationResult, RAGProvider


class OllamaProvider(RAGProvider):
    name = "ollama"

    def __init__(self, llm_model: str | None = None, embedding_model: str | None = None):
        self.base = settings.ollama_base_url.rstrip("/")
        self.embedding_model = embedding_model or settings.ollama_embedding_model
        self.llm_model = llm_model or settings.ollama_llm_model

    def embed(self, texts: list[str], task: str = "document") -> list[list[float]]:
        r = requests.post(f"{self.base}/api/embed", json={"model": self.embedding_model, "input": texts}, timeout=45)
        if r.status_code == 404:
            result = []
            for text in texts:
                old = requests.post(f"{self.base}/api/embeddings", json={"model": self.embedding_model, "prompt": text}, timeout=45)
                old.raise_for_status()
                result.append([float(x) for x in old.json()["embedding"]])
            return result
        r.raise_for_status()
        return [[float(x) for x in row] for row in r.json().get("embeddings", [])]

    def generate(self, prompt: str) -> GenerationResult:
        r = requests.post(f"{self.base}/api/generate", json={"model": self.llm_model, "prompt": prompt, "stream": False}, timeout=60)
        r.raise_for_status()
        data = r.json()
        return GenerationResult(text=str(data.get("response", "")).strip(), raw=data, input_tokens=data.get("prompt_eval_count"), output_tokens=data.get("eval_count"))
