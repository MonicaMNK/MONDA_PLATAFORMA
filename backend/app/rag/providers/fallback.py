from __future__ import annotations

from .base import GenerationResult, RAGProvider


class FallbackProvider(RAGProvider):
    name = "fallback"
    embedding_model = "fallback-lexical-v1"
    llm_model = "fallback-extractive-v1"

    @property
    def supports_embeddings(self) -> bool:
        return False

    @property
    def supports_generation(self) -> bool:
        return False

    def embed(self, texts: list[str], task: str = "document") -> list[list[float]]:
        return []

    def generate(self, prompt: str) -> GenerationResult:
        return GenerationResult(text="")
