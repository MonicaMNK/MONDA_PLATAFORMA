from __future__ import annotations

from ...core.config import settings
from .base import RAGProvider
from .fallback import FallbackProvider
from .gemini import GeminiProvider
from .ollama import OllamaProvider


class ExternalProviderAuthorizationRequired(RuntimeError):
    """Raised before any content is sent to an unauthorized external provider."""


def _gemini_authorized() -> bool:
    return bool(settings.gemini_external_processing_authorized)


def get_provider(mode: str | None = None, *, llm_model: str | None = None, llm_fallback_models: list[str] | None = None, embedding_model: str | None = None, ollama_model: str | None = None) -> RAGProvider:
    chosen = (mode or settings.rag_mode or "fallback").lower()
    if chosen == "gemini":
        if not _gemini_authorized():
            raise ExternalProviderAuthorizationRequired(
                "Gemini está bloqueado: falta autorización institucional para procesamiento externo."
            )
        return GeminiProvider(llm_model=llm_model, fallback_models=llm_fallback_models, embedding_model=embedding_model)
    if chosen == "ollama":
        return OllamaProvider(llm_model=ollama_model or llm_model, embedding_model=embedding_model)
    if chosen == "auto":
        if settings.gemini_api_key:
            if not _gemini_authorized():
                raise ExternalProviderAuthorizationRequired(
                    "Gemini está bloqueado: falta autorización institucional para procesamiento externo."
                )
            return GeminiProvider(llm_model=llm_model, fallback_models=llm_fallback_models, embedding_model=embedding_model)
        return FallbackProvider()
    return FallbackProvider()


def get_provider_with_fallback(mode: str | None = None, **kwargs) -> tuple[RAGProvider, str | None]:
    try:
        return get_provider(mode, **kwargs), None
    except Exception as exc:
        if settings.rag_allow_fallback:
            return FallbackProvider(), str(exc)
        raise
