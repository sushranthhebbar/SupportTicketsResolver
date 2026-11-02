"""Provider-neutral configuration for OpenAI-compatible model APIs."""

from __future__ import annotations

import os


DEFAULT_MODEL_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def resolve_api_key(explicit_key: str | None = None) -> str | None:
    """Use explicit, generic, Groq, then legacy OpenRouter credentials."""
    return (
        explicit_key
        or os.getenv("MODEL_API_KEY")
        or os.getenv("GROQ_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
    )


def resolve_api_url(explicit_url: str | None = None) -> str:
    """Resolve explicit, generic, legacy, then default chat-completions URL."""
    return (
        explicit_url
        or os.getenv("MODEL_API_URL")
        or os.getenv("OPENROUTER_API_URL")
        or DEFAULT_MODEL_API_URL
    )
