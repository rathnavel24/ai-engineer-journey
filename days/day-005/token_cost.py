"""Day 5: token counts and a cost-per-1,000-alerts projection for two models.

tiktoken only understands OpenAI's own tokenizers, so the two models here are
counted differently:
  - gpt-4o is counted with its real encoding (o200k_base, resolved via
    tiktoken.encoding_for_model("gpt-4o")) - this is an exact count of what
    OpenAI would actually bill.
  - claude-sonnet-5 has no tiktoken encoding at all - Anthropic uses its own
    BPE vocabulary, not one of tiktoken's. We approximate it with cl100k_base
    (GPT-4's older general-purpose English encoding) as a stand-in and flag
    every Claude number below as an ESTIMATE. A real count would require
    Anthropic's own token-counting endpoint (client.messages.count_tokens),
    not tiktoken.

Pricing is hand-entered from each provider's own current pricing page (see
answers.md for links and the date checked) - tiktoken has no pricing data,
and prices move, so these numbers are not sourced from training-data memory.

Run: uv run python days/day-005/token_cost.py
"""

import tiktoken

from alerts import ALERTS

OUTPUT_TOKENS_PER_ALERT = 40  # assumed ~40-token summary returned per alert

MODELS = {
    "gpt-4o": {
        "encoding": tiktoken.encoding_for_model("gpt-4o"),  # o200k_base, exact
        "approx": False,
        "input_price_per_1m": 2.50,
        "output_price_per_1m": 10.00,
    },
    "claude-sonnet-5": {
        # cl100k_base approximation - see module docstring
        "encoding": tiktoken.get_encoding("cl100k_base"),
        "approx": True,
        "input_price_per_1m": 2.00,
        "output_price_per_1m": 10.00,
    },
}


def main() -> None:
    for model_name, cfg in MODELS.items():
        encoding = cfg["encoding"]
        counts = [len(encoding.encode(alert)) for alert in ALERTS]
        total_input_tokens = sum(counts)
        avg_input_tokens = total_input_tokens / len(ALERTS)

        tag = "APPROXIMATED via cl100k_base" if cfg["approx"] else "exact, o200k_base"
        print(f"\n=== {model_name} ({tag}) ===")
        print(f"{'alert index':>11}  {'token count':>11}")
        for i, c in enumerate(counts):
            print(f"{i:>11}  {c:>11}")

        max_i = max(range(len(counts)), key=lambda i: counts[i])
        min_i = min(range(len(counts)), key=lambda i: counts[i])
        print(f"\nMost expensive alert: index {max_i} ({counts[max_i]} tokens) - {ALERTS[max_i]!r}")
        print(f"Cheapest alert:       index {min_i} ({counts[min_i]} tokens) - {ALERTS[min_i]!r}")

        print(f"\nTotal input tokens across {len(ALERTS)} alerts: {total_input_tokens}")
        print(f"Avg input tokens/alert: {avg_input_tokens:.2f}")

        input_price_per_token = cfg["input_price_per_1m"] / 1_000_000
        output_price_per_token = cfg["output_price_per_1m"] / 1_000_000

        cost_per_1000 = (
            avg_input_tokens * input_price_per_token
            + OUTPUT_TOKENS_PER_ALERT * output_price_per_token
        ) * 1000

        print(
            f"Pricing: ${cfg['input_price_per_1m']:.2f}/1M input, "
            f"${cfg['output_price_per_1m']:.2f}/1M output"
        )
        print(
            f"Projected cost per 1,000 alerts "
            f"(avg {avg_input_tokens:.2f} in + {OUTPUT_TOKENS_PER_ALERT} out tokens each): "
            f"${cost_per_1000:.4f}"
        )


if __name__ == "__main__":
    main()
