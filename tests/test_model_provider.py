from src.model_provider import DEFAULT_MODEL_API_URL, resolve_api_key, resolve_api_url


def test_provider_configuration_prefers_generic_settings(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "generic-key")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "router-key")
    monkeypatch.setenv("MODEL_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    monkeypatch.setenv("OPENROUTER_API_URL", "https://openrouter.example/chat/completions")

    assert resolve_api_key() == "generic-key"
    assert resolve_api_url() == "https://api.groq.com/openai/v1/chat/completions"
    assert resolve_api_key("explicit-key") == "explicit-key"


def test_provider_configuration_keeps_legacy_openrouter_compatibility(monkeypatch):
    for name in ("MODEL_API_KEY", "GROQ_API_KEY", "MODEL_API_URL", "OPENROUTER_API_URL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "legacy-router-key")

    assert resolve_api_key() == "legacy-router-key"
    assert resolve_api_url() == DEFAULT_MODEL_API_URL


def test_groq_key_can_be_used_without_provider_specific_code(monkeypatch):
    for name in ("MODEL_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")

    assert resolve_api_key() == "groq-key"
