from types import SimpleNamespace

import pytest
import requests

from backend.app.rag.providers.fallback import FallbackProvider
from backend.app.rag.providers.factory import get_provider_with_fallback


def test_gemini_is_never_constructed_without_external_processing_authorization(monkeypatch):
    import backend.app.rag.providers.factory as provider_factory

    monkeypatch.setattr(provider_factory, 'settings', SimpleNamespace(
        gemini_external_processing_authorized=False,
        gemini_api_key='configured-test-key',
        rag_allow_fallback=True,
    ))
    def forbidden_provider(**_kwargs):
        raise AssertionError('Gemini provider must not be constructed before authorization')
    monkeypatch.setattr(provider_factory, 'GeminiProvider', forbidden_provider)

    provider, warning = get_provider_with_fallback('auto')
    assert isinstance(provider, FallbackProvider)
    assert 'autorizaci' in warning.lower()
    provider, warning = get_provider_with_fallback('gemini')
    assert isinstance(provider, FallbackProvider)
    assert warning


@pytest.mark.parametrize("failure", ["http_503", "timeout", "empty"])
def test_gemini_generation_uses_configured_backup_after_primary_failure(monkeypatch, failure):
    import backend.app.rag.providers.gemini as gemini_module

    monkeypatch.setattr(gemini_module, "settings", SimpleNamespace(
        gemini_api_key="synthetic-key",
        gemini_embedding_model="embedding-test",
        gemini_llm_model="primary-model",
        gemini_llm_fallback_models=["backup-model"],
        gemini_base_url="https://example.invalid/v1beta",
    ))
    calls = []

    class Response:
        def __init__(self, status, payload):
            self.status_code = status
            self.ok = status < 400
            self.payload = payload

        def json(self):
            return self.payload

    def post(url, **_kwargs):
        calls.append(url)
        if "primary-model" in url:
            if failure == "timeout":
                raise requests.Timeout("synthetic timeout")
            if failure == "http_503":
                return Response(503, {})
            return Response(200, {"candidates": []})
        return Response(200, {
            "candidates": [{"content": {"parts": [{"text": "Respuesta con fuente [F1]."}]}}],
            "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 4},
        })

    monkeypatch.setattr(gemini_module.requests, "post", post)
    provider = gemini_module.GeminiProvider()

    generated = provider.generate("prompt sintético")

    assert generated.text == "Respuesta con fuente [F1]."
    assert provider.last_generation_model == "backup-model"
    assert provider.last_generation_warning
    assert len(calls) == 2


def test_gemini_generation_fails_closed_when_all_models_fail(monkeypatch):
    import backend.app.rag.providers.gemini as gemini_module

    monkeypatch.setattr(gemini_module, "settings", SimpleNamespace(
        gemini_api_key="synthetic-key",
        gemini_embedding_model="embedding-test",
        gemini_llm_model="primary-model",
        gemini_llm_fallback_models=["backup-model"],
        gemini_base_url="https://example.invalid/v1beta",
    ))

    class FailedResponse:
        ok = False
        status_code = 503

    monkeypatch.setattr(gemini_module.requests, "post", lambda *_args, **_kwargs: FailedResponse())
    provider = gemini_module.GeminiProvider()

    with pytest.raises(RuntimeError, match="Todos los modelos Gemini"):
        provider.generate("prompt sintético")
