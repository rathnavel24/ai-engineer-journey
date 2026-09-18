"""Day 2: send the same prompt to Gemini, OpenRouter, and a local Ollama model
and compare latency, token usage, and cost.

Gemini pricing source: https://ai.google.dev/gemini-api/docs/pricing (checked 2026-09-18).
OpenRouter's cost is read directly from its response `usage.cost` field (USD,
matches the underlying provider's rate - see https://openrouter.ai/docs/use-cases/usage-accounting).
Ollama runs on local compute, so its cost is always $0.
"""

import os
import statistics
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass

import requests
from dotenv import load_dotenv
from google import genai

load_dotenv()

PROMPT = "In one sentence, explain what a vector database is."
RUNS = 3

# USD per 1M tokens: (input, output). Gemini rate is the through-2026-12-31 promo rate.
PRICING = {
    "gemini-3.6-flash": (0.75, 3.75),
    "ollama": (0.0, 0.0),
}


@dataclass
class Result:
    provider: str
    model: str
    latency_s: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    output_text: str | None = None
    error: str | None = None


def compute_cost(pricing_key: str, input_tokens: int, output_tokens: int) -> float:
    input_rate, output_rate = PRICING[pricing_key]
    return (input_tokens / 1_000_000) * input_rate + (output_tokens / 1_000_000) * output_rate


def call_gemini(prompt: str) -> Result:
    model = "gemini-3.6-flash"
    result = Result(provider="Gemini", model=model)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        result.error = "GEMINI_API_KEY not set"
        return result

    try:
        client = genai.Client(api_key=api_key)
        start = time.perf_counter()
        response = client.models.generate_content(model=model, contents=prompt)
        result.latency_s = time.perf_counter() - start

        usage = response.usage_metadata
        result.input_tokens = usage.prompt_token_count
        result.output_tokens = usage.candidates_token_count
        result.cost_usd = compute_cost(model, result.input_tokens, result.output_tokens)
        result.output_text = response.text.strip()
    except Exception as e:
        result.error = str(e)

    return result


def call_openrouter(prompt: str) -> Result:
    # Free-tier model by default so this runs with a zero-balance key;
    # set OPENROUTER_MODEL to a paid model once credits are loaded.
    model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash-0731:free")
    result = Result(provider="OpenRouter", model=model)

    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        result.error = "OPEN_ROUTER_API_KEY not set"
        return result

    try:
        start = time.perf_counter()
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}]},
            timeout=60,
        )
        result.latency_s = time.perf_counter() - start
        response.raise_for_status()

        data = response.json()
        usage = data["usage"]
        result.input_tokens = usage["prompt_tokens"]
        result.output_tokens = usage["completion_tokens"]
        result.cost_usd = usage["cost"]  # OpenRouter reports actual USD cost directly
        result.output_text = data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        result.error = str(e)

    return result


def call_ollama(prompt: str) -> Result:
    host = os.getenv("OLLAMA_HOST") or "http://localhost:11434"
    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    result = Result(provider="Ollama", model=model)

    try:
        start = time.perf_counter()
        response = requests.post(
            f"{host}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        result.latency_s = time.perf_counter() - start
        response.raise_for_status()

        data = response.json()
        result.input_tokens = data.get("prompt_eval_count", 0)
        result.output_tokens = data.get("eval_count", 0)
        result.cost_usd = compute_cost("ollama", result.input_tokens, result.output_tokens)
        result.output_text = data.get("response", "").strip()
    except Exception as e:
        result.error = str(e)

    return result


def run_with_median(call_fn: Callable[[str], Result], prompt: str, runs: int = RUNS) -> Result:
    """Call call_fn `runs` times and collapse the attempts into one Result using
    the median latency/tokens/cost across the successful runs."""
    attempts = [call_fn(prompt) for _ in range(runs)]
    successes = [r for r in attempts if r.error is None]

    if not successes:
        return attempts[0]  # every run failed - surface the first error as-is

    return Result(
        provider=successes[0].provider,
        model=successes[0].model,
        latency_s=statistics.median(r.latency_s for r in successes),
        input_tokens=round(statistics.median(r.input_tokens for r in successes)),
        output_tokens=round(statistics.median(r.output_tokens for r in successes)),
        cost_usd=statistics.median(r.cost_usd for r in successes),
        output_text=successes[-1].output_text,
    )


def print_report(results: list[Result]) -> None:
    print(f'Prompt: "{PROMPT}"')
    print(f"(each provider called {RUNS}x; latency/tokens/cost below are medians)\n")

    header = f"{'Provider':<12}{'Model':<38}{'Latency (s)':<14}{'In tok':<9}{'Out tok':<9}{'Cost ($)':<12}"
    print(header)
    print("-" * len(header))

    for r in results:
        if r.error:
            print(f"{r.provider:<12}{r.model:<38}FAILED: {r.error}")
            continue

        print(
            f"{r.provider:<12}{r.model:<38}{r.latency_s:<14.3f}"
            f"{r.input_tokens:<9}{r.output_tokens:<9}{r.cost_usd:<12.8f}"
        )

    print()
    for r in results:
        if not r.error:
            print(f"{r.provider} output: {r.output_text}")


def main() -> int:
    results = [
        run_with_median(call_gemini, PROMPT),
        run_with_median(call_openrouter, PROMPT),
        run_with_median(call_ollama, PROMPT),
    ]
    print_report(results)
    return 0 if all(r.error is None for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
