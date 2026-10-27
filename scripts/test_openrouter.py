"""Send one small, free-model request to verify the OpenRouter API setup."""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")

    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("MODEL_NAME")

    if not api_key or api_key == "your_key_here":
        print("Missing OPENROUTER_API_KEY in the project-root .env file.")
        return 1
    if not model:
        print("Missing MODEL_NAME in the project-root .env file.")
        return 1
    if model != "openrouter/free" and not model.endswith(":free"):
        print(
            f"MODEL_NAME is '{model}', which is not explicitly a free model. "
            "For a no-cost smoke test, set MODEL_NAME in .env to openrouter/free "
            "or to an available OpenRouter model ending in :free."
        )
        return 1

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": "Reply with exactly: API connection works."}
                ],
                "max_tokens": 20,
            },
            timeout=60,
        )
    except requests.RequestException as exc:
        print(f"Could not reach OpenRouter: {exc}")
        return 1

    if not response.ok:
        try:
            detail = response.json().get("error", {}).get("message", response.text)
        except ValueError:
            detail = response.text
        print(f"OpenRouter returned HTTP {response.status_code}: {detail}")
        return 1

    try:
        result = response.json()
        message = result["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        print("OpenRouter responded, but the response did not contain a chat message.")
        return 1

    print(f"Success using {result.get('model', model)}:")
    print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
