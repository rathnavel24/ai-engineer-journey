"""Detect and validate API keys - from .env or pasted in directly - against each
provider's API. Validation calls only list models (no completion tokens billed).

Usage:
    uv run python scripts/test_apikeys.py                 # checks .env, then prompts for pasted keys
    uv run python scripts/test_apikeys.py sk-ant-...       # also checks keys passed as arguments
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def detect_provider(key: str) -> str | None:
    if key.startswith("sk-ant-"):
        return "anthropic"
    if key.startswith("sk-or-"):
        return "openrouter"
    if key.startswith("sk-"):
        return "openai"
    if key.startswith("AIza") or key.startswith("AQ."):
        return "gemini"
    return None


def validate_anthropic(key: str) -> tuple[bool, str]:
    import anthropic

    try:
        client = anthropic.Anthropic(api_key=key)
        first = next(iter(client.models.list()), None)
        return True, f"OK - e.g. {first.id}" if first else "OK"
    except anthropic.AuthenticationError:
        return False, "invalid key"
    except Exception as e:
        return False, str(e)


def validate_openai(key: str) -> tuple[bool, str]:
    import openai

    try:
        client = openai.OpenAI(api_key=key)
        first = next(iter(client.models.list()), None)
        return True, f"OK - e.g. {first.id}" if first else "OK"
    except openai.AuthenticationError:
        return False, "invalid key"
    except Exception as e:
        return False, str(e)


def validate_openrouter(key: str) -> tuple[bool, str]:
    import openai

    try:
        client = openai.OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1")
        first = next(iter(client.models.list()), None)
        return True, f"OK - e.g. {first.id}" if first else "OK"
    except openai.AuthenticationError:
        return False, "invalid key"
    except Exception as e:
        return False, str(e)


def validate_gemini(key: str) -> tuple[bool, str]:
    from google.genai import Client, errors

    try:
        client = Client(api_key=key)
        first = next(iter(client.models.list()), None)
        return True, f"OK - e.g. {first.name}" if first else "OK"
    except errors.ClientError as e:
        return False, f"invalid key ({e})"
    except Exception as e:
        return False, str(e)


VALIDATORS = {
    "anthropic": validate_anthropic,
    "openai": validate_openai,
    "openrouter": validate_openrouter,
    "gemini": validate_gemini,
}


def check_key(label: str, key: str) -> bool | None:
    """Returns True/False for a validated key, or None if it was skipped."""
    key = key.strip()
    if not key:
        print(f"{label}: SKIPPED (empty)")
        return None

    provider = detect_provider(key)
    if provider is None:
        print(f"{label}: UNKNOWN FORMAT - can't tell which provider this key belongs to")
        return None

    ok, detail = VALIDATORS[provider](key)
    print(f"{label} [{provider}]: {'VALID' if ok else 'INVALID'} - {detail}")
    return ok


def main() -> int:
    outcomes: list[bool | None] = []

    for label, env_name in [
        ("OPENAI_API_KEY", "OPENAI_API_KEY"),
        ("OPEN_ROUTER_API_KEY", "OPEN_ROUTER_API_KEY"),
        ("GEMINI_API_KEY", "GEMINI_API_KEY"),
    ]:
        outcomes.append(check_key(label, os.getenv(env_name, "")))

    pasted_keys = sys.argv[1:]
    if pasted_keys:
        for i, key in enumerate(pasted_keys, start=1):
            outcomes.append(check_key(f"pasted key #{i}", key))
    elif sys.stdin.isatty():
        print("\nPaste a key to test (Enter with nothing to finish):")
        while True:
            key = input("> ")
            if not key.strip():
                break
            outcomes.append(check_key("pasted key", key))

    return 1 if any(o is False for o in outcomes) else 0


if __name__ == "__main__":
    sys.exit(main())
