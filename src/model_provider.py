"""Provider-neutral configuration for OpenAI-compatible model APIs."""

from __future__ import annotations

import logging
import os
import re
import threading
import time
from typing import Any, Callable


DEFAULT_MODEL_API_URL = "https://openrouter.ai/api/v1/chat/completions"
logger = logging.getLogger(__name__)
PLACEHOLDER_API_KEYS = frozenset({"your_key_here", "your_groq_api_key", "set_a_long_random_agent_token"})
_request_pacing_lock = threading.Lock()
_last_request_at: float | None = None


def _parse_provider_duration(value: Any) -> float | None:
    """Parse provider reset values such as ``47.1s`` or ``1h22m4.8s``."""
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        pass

    text = str(value).strip()
    parts = re.findall(r"(\d+(?:\.\d+)?)(h|m|s)", text)
    if not parts or "".join(number + unit for number, unit in parts) != text:
        return None
    units = {"h": 3600.0, "m": 60.0, "s": 1.0}
    return sum(float(number) * units[unit] for number, unit in parts)


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


def has_configured_api_key(api_key: str | None) -> bool:
    """Return false for missing and documented placeholder credentials."""
    return bool(api_key and api_key.strip() and api_key.strip() not in PLACEHOLDER_API_KEYS)


def post_with_rate_limit_retry(
    requester: Any,
    url: str,
    *,
    sleeper: Callable[[float], None] = time.sleep,
    max_retries: int | None = None,
    **kwargs: Any,
) -> Any:
    """Retry HTTP 429 responses, honoring Retry-After when the provider supplies it."""
    retries = max_retries
    if retries is None:
        retries = int(os.getenv("MODEL_429_MAX_RETRIES", "5"))
    retries = max(0, retries)
    fallback_seconds = float(os.getenv("MODEL_429_FALLBACK_SECONDS", "5"))
    fallback_seconds = max(0.0, fallback_seconds)
    min_interval = max(0.0, float(os.getenv("MODEL_MIN_REQUEST_INTERVAL_SECONDS", "0")))

    for attempt in range(retries + 1):
        global _last_request_at
        with _request_pacing_lock:
            now = time.monotonic()
            wait_seconds = (
                max(0.0, min_interval - (now - _last_request_at))
                if _last_request_at is not None
                else 0.0
            )
            if wait_seconds:
                logger.info("Pacing model request: waiting %.1f seconds.", wait_seconds)
                sleeper(wait_seconds)
            _last_request_at = time.monotonic()
        response = requester.post(url, **kwargs)
        status = getattr(response, "status_code", getattr(response, "status", 200))
        if status != 429:
            return response
        if attempt >= retries:
            logger.error("Model provider is still rate limiting after %d retries.", retries)
            return response

        headers = getattr(response, "headers", {}) or {}
        retry_after = headers.get("Retry-After") or headers.get("retry-after")
        delay = _parse_provider_duration(retry_after)
        if delay is None:
            delay = min(60.0, fallback_seconds * (2 ** attempt))
        token_reset = _parse_provider_duration(
            headers.get("x-ratelimit-reset-tokens")
        )
        if token_reset is not None:
            delay = max(delay, token_reset)
        logger.warning(
            "Model provider rate limited the request (HTTP 429); retry %d/%d in %.1f seconds. "
            "Request budget remaining=%s, reset=%s; token budget remaining=%s, reset=%s.",
            attempt + 1,
            retries,
            delay,
            headers.get("x-ratelimit-remaining-requests", "unknown"),
            headers.get("x-ratelimit-reset-requests", "unknown"),
            headers.get("x-ratelimit-remaining-tokens", "unknown"),
            headers.get("x-ratelimit-reset-tokens", "unknown"),
        )
        sleeper(delay)

    return response
