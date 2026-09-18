import os
import sys

from dotenv import load_dotenv

REQUIRED_KEYS = ["ANTHROPIC_API_KEY", "OPEN_ROUTER_API_KEY", "GEMINI_API_KEY", "OLLAMA_HOST"]


def main() -> int:
    load_dotenv()

    missing = [key for key in REQUIRED_KEYS if not os.getenv(key)]

    for key in REQUIRED_KEYS:
        status = "OK" if os.getenv(key) else "MISSING"
        print(f"{key}: {status}")

    if missing:
        print(f"\nMissing/empty: {', '.join(missing)}")
        return 1

    print("\nAll required environment variables are set.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
