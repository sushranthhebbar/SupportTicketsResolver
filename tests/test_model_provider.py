from src.model_provider import (
    DEFAULT_MODEL_API_URL,
    has_configured_api_key,
    post_with_rate_limit_retry,
    resolve_api_key,
    resolve_api_url,
)


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


def test_placeholder_groq_key_is_not_usable():
    assert not has_configured_api_key("your_groq_api_key")
    assert not has_configured_api_key(None)
    assert has_configured_api_key("actual-api-key")


def test_rate_limit_retries_honor_retry_after_then_returns_success():
    class Response:
        def __init__(self, status, retry_after=None):
            self.status_code = status
            self.headers = {"Retry-After": str(retry_after)} if retry_after is not None else {}

    class Requester:
        def __init__(self):
            self.responses = [Response(429, 3), Response(200)]
            self.calls = 0

        def post(self, _url, **_kwargs):
            self.calls += 1
            return self.responses.pop(0)

    requester = Requester()
    waits = []
    result = post_with_rate_limit_retry(
        requester, "https://provider.test/chat", sleeper=waits.append
    )
    assert result.status_code == 200
    assert requester.calls == 2
    assert waits == [3.0]


def test_rate_limit_waits_for_token_window_reset_when_longer_than_retry_after():
    class Response:
        def __init__(self, status):
            self.status_code = status
            self.headers = (
                {
                    "Retry-After": "7",
                    "x-ratelimit-remaining-requests": "943",
                    "x-ratelimit-reset-requests": "1h22m4.8s",
                    "x-ratelimit-remaining-tokens": "3117",
                    "x-ratelimit-reset-tokens": "47.1s",
                }
                if status == 429
                else {}
            )

    class Requester:
        def __init__(self):
            self.responses = [Response(429), Response(200)]

        def post(self, _url, **_kwargs):
            return self.responses.pop(0)

    waits = []
    result = post_with_rate_limit_retry(
        Requester(), "https://provider.test/chat", sleeper=waits.append
    )
    assert result.status_code == 200
    assert waits == [47.1]


def test_rate_limit_retry_is_bounded():
    class Response:
        status_code = 429
        headers = {"Retry-After": "0"}

    class Requester:
        def __init__(self):
            self.calls = 0

        def post(self, _url, **_kwargs):
            self.calls += 1
            return Response()

    requester = Requester()
    waits = []
    result = post_with_rate_limit_retry(
        requester,
        "https://provider.test/chat",
        sleeper=waits.append,
        max_retries=2,
    )
    assert result.status_code == 429
    assert requester.calls == 3
    assert waits == [0.0, 0.0]
