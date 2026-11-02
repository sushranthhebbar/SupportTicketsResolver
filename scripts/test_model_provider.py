"""Make one small request to verify the configured OpenAI-compatible provider."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.model_provider import resolve_api_key, resolve_api_url  # noqa: E402


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = resolve_api_key()
    model = os.getenv("MODEL_NAME")
    if not api_key or api_key in {"your_key_here", "your_groq_api_key"}:
        print("Set MODEL_API_KEY (or a supported legacy provider key) in .env.")
        return 1
    if not model:
        print("Set MODEL_NAME in the project-root .env file.")
        return 1

    url = resolve_api_url()
    try:
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Reply with exactly: API connection works."}],
                "response_format": {"type": "json_object"},
                "temperature": 0,
                "max_tokens": 30,
            },
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        message = result["choices"][0]["message"]["content"]
    except requests.RequestException as exc:
        detail = ""
        if getattr(exc, "response", None) is not None:
            try:
                detail = exc.response.json().get("error", {}).get("message", "")
            except ValueError:
                detail = exc.response.text
        print(f"Provider request failed: {type(exc).__name__}: {detail or exc}")
        return 1
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        print(f"Provider returned an unexpected response: {type(exc).__name__}: {exc}")
        return 1

    print(f"Success using {result.get('model', model)} at {url}:")
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
