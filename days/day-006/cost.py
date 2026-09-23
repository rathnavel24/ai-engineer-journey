"""Day 6: cost estimation, reusing Day 5's pricing constants directly instead
of retyping them - a second hand-typed copy of a price is exactly the kind
of thing that quietly drifts out of sync when a provider changes a rate.

Day 5's MODELS dict only has real pricing for "gpt-4o" and "claude-sonnet-5"
(the two models priced there from the provider's own pricing page). This
app actually calls Ollama and Gemini, neither of which Day 5 priced - Ollama
is genuinely free (local compute, no per-token bill), and Gemini was simply
never priced. Rather than invent a Gemini number here, estimate_cost()
returns 0.0 for any model it doesn't recognize and callers are expected to
treat that as "untracked," not "actually free." See answers.md.
"""

import sys
from pathlib import Path

_DAY_005 = Path(__file__).resolve().parent.parent / "day-005"
if str(_DAY_005) not in sys.path:
    sys.path.insert(0, str(_DAY_005))

from token_cost import MODELS  # noqa: E402  (Day 5's pricing constants)


def estimate_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
    """Cost in USD for one request, using Day 5's per-model pricing.

    Returns 0.0 (untracked, not "free") for any model Day 5 didn't price.
    """
    pricing = MODELS.get(model)
    if pricing is None:
        return 0.0

    input_cost = prompt_tokens * (pricing["input_price_per_1m"] / 1_000_000)
    output_cost = completion_tokens * (pricing["output_price_per_1m"] / 1_000_000)
    return input_cost + output_cost


if __name__ == "__main__":
    print(f"gpt-4o: ${estimate_cost(26, 40, 'gpt-4o'):.6f}")
    print(f"claude-sonnet-5: ${estimate_cost(26, 40, 'claude-sonnet-5'):.6f}")
    print(f"llama3.2:3b (untracked): ${estimate_cost(26, 40, 'llama3.2:3b'):.6f}")
