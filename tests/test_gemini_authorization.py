from types import SimpleNamespace

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
