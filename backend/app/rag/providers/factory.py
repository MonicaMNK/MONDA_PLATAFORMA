from __future__ import annotations

from ...core.config import settings
from .base import RAGProvider
from .fallback import FallbackProvider
from .gemini import GeminiProvider
from .ollama import OllamaProvider


def get_provider(mode: str | None = None, *, llm_model: str | None = None, embedding_model: str | None = None, ollama_model: str | None = None) -> RAGProvider:
    chosen = (mode or settings.rag_mode or "fallback").lower()
    if chosen == "gemini":
        return GeminiProvider(llm_model=llm_model, embedding_model=embedding_model)
    if chosen == "ollama":
        return OllamaProvider(llm_model=ollama_model or llm_model, embedding_model=embedding_model)
    if chosen == "auto":
        if settings.gemini_api_key:
            return GeminiProvider(llm_model=llm_model, embedding_model=embedding_model)
        return FallbackProvider()
    return FallbackProvider()


def get_provider_with_fallback(mode: str | None = None, **kwargs) -> tuple[RAGProvider, str | None]:
    try:
        return get_provider(mode, **kwargs), None
    except Exception as exc:
        if settings.rag_allow_fallback:
            return FallbackProvider(), str(exc)
        raise
