"""Day 2: verify the Gemini API key and the local Ollama model both respond."""

import os
import sys

import requests
from dotenv import load_dotenv
from google import genai

load_dotenv()

PROMPT = "Reply with exactly one word: pong"


def test_gemini() -> bool:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Gemini: SKIPPED (GEMINI_API_KEY not set)")
        return False

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=PROMPT,
        )
        print(f"Gemini: OK -> {response.text.strip()}")
        return True
    except Exception as e:
        print(f"Gemini: FAILED -> {e}")
        return False


def test_ollama() -> bool:
    host = os.getenv("OLLAMA_HOST") or "http://localhost:11434"
    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    try:
        response = requests.post(
            f"{host}/api/generate",
            json={"model": model, "prompt": PROMPT, "stream": False},
            timeout=30,
        )
        response.raise_for_status()
        text = response.json().get("response", "").strip()
        print(f"Ollama ({model} @ {host}): OK -> {text}")
        return True
    except Exception as e:
        print(f"Ollama ({model} @ {host}): FAILED -> {e}")
        return False


def main() -> int:
    results = [test_gemini(), test_ollama()]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
