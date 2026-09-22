# Day 5

## Token counts and cost projection

Encodings used:
- **gpt-4o** — exact. `tiktoken.encoding_for_model("gpt-4o")` resolves to `o200k_base`, the real encoding OpenAI bills against.
- **claude-sonnet-5** — **approximated**. tiktoken has no Anthropic encoding at all (Anthropic uses its own BPE vocabulary), so this uses `tiktoken.get_encoding("cl100k_base")` (GPT-4's older general-purpose English encoding) as a stand-in. Every claude-sonnet-5 number below is an estimate, not a measurement — a real count would need Anthropic's own `client.messages.count_tokens` endpoint, not tiktoken.

| alert index | token count |
|---|---|
| 0 | 22 |
| 1 | 29 |
| 2 | 28 |
| 3 | 22 |
| 4 | 29 |
| 5 | 28 |
| 6 | 22 |
| 7 | 29 |
| 8 | 28 |
| 9 | 22 |
| 10 | 29 |
| 11 | 28 |
| 12 | 22 |
| 13 | 29 |
| 14 | 28 |
| 15 | 22 |
| 16 | 28 |
| 17 | 27 |
| 18 | 21 |
| 19 | 29 |

(Identical for both models here — `o200k_base` and `cl100k_base` happen to segment this particular alert vocabulary the same way. That's a coincidence of this small, plain-English string set, not something to expect in general — the whole point of flagging the Claude column as an approximation is that a real Claude tokenizer could easily disagree.)

Most expensive alert: index 1, 29 tokens — `"Machine M-02 energy draw 4.8kW exceeds threshold 4.0kW, tenant=acme, severity=medium"`
Cheapest alert: index 18, 21 tokens — `"Machine M-15 temperature 99C exceeds threshold 85C, tenant=wayne, severity=critical"`

Total input tokens across 20 alerts: **522** (both models, per above)
Avg input tokens/alert: **26.10**
Assumed output: 40 tokens/alert (given)

### Pricing (sourced from each provider's own pricing page, checked 2026-09-22)

| Model | Input $/1M | Output $/1M | Source |
|---|---|---|---|
| gpt-4o | $2.50 | $10.00 | [OpenAI API Pricing](https://developers.openai.com/api/docs/pricing) |
| claude-sonnet-5 | $2.00 | $10.00 | [Claude Pricing](https://claude.com/pricing) |

### Cost per 1,000 alerts

`(avg_input_tokens/alert + avg_output_tokens/alert) × price-per-token × 1000`, computed separately per token type:

- **gpt-4o**: (26.10 × $2.50/1M) + (40 × $10.00/1M), × 1000 alerts = **$0.4653** per 1,000 alerts
- **claude-sonnet-5 (estimate)**: (26.10 × $2.00/1M) + (40 × $10.00/1M), × 1000 alerts = **$0.4522** per 1,000 alerts

Run it yourself: `uv run python days/day-005/token_cost.py`

---

## Exercises

**1. Explain in your own words: why can the same alert string produce a different token count depending on which model's encoding you use?**

A tokenizer's vocabulary isn't universal — it's the output of running byte-pair encoding over that provider's own training corpus, merging whichever byte/character pairs showed up most often *in that corpus*, until it hits its target vocabulary size (GPT-4o's `o200k_base` has a different merge list than Claude's tokenizer, which has a different one again). Two tokenizers looking at the exact same string can legally chunk it differently — one might have `"temperature"` as a single merged token because it was common enough in its training data to earn its own slot, while another splits it into `"temp"` + `"erature"` or smaller pieces because that word pair never got merged in its vocabulary. Same characters in, different chunk boundaries out, so different token counts — the string didn't change, the ruler measuring it did.

**3. What breaks if: a user-submitted alert message is 50,000 characters long and you feed it straight into your prompt with no length check against the model's context window?**

At ~4 characters/token that's roughly 12,500 tokens from one field alone — before you've added the system prompt, instructions, or any other context. A few things can go wrong depending on where the ceiling actually bites:

- If the full prompt (this alert + everything else) exceeds the model's context window, the API just rejects the request outright — a 400-style error, not a truncated-but-usable response. Your pipeline needs to handle that as a real failure case, not assume every request succeeds.
- If some upstream layer *silently* truncates instead of rejecting, you can lose the part of the alert that actually mattered (e.g. the threshold value or the tenant field gets cut off), and now you're generating a confident summary of an incomplete alert — a worse failure than an outright error because nothing visibly broke.
- Even short of the hard limit, one 50,000-character alert can quietly dominate your token budget/cost for that batch — a single malformed or adversarial input costs as much as hundreds of normal ~26-token alerts, which is exactly the kind of thing a per-request length check (reject, truncate with a warning, or summarize before it ever reaches the model) is supposed to catch before it hits the API at all.

**4. Pick your two models: do they price input and output tokens the same, or differently? Write one sentence on why a provider might price them differently.**

Different for both: gpt-4o is $2.50 in / $10.00 out (4x), claude-sonnet-5 is $2.00 in / $10.00 out (5x). Output costs more per token because generating it is inherently sequential — the model does a full forward pass to produce *each* output token one at a time (autoregressively, each one conditioned on all the ones before it) — while the input prompt gets processed in one parallel forward pass across every token at once, so a token of output consumes meaningfully more compute than a token of input.

---

## Karpathy — "Deep Dive into LLMs like ChatGPT," Tokenization → Inference (10 notes, in my own words)

1. Text has to become numbers before a neural net can touch it. The naive approach — every character as its raw bits (1s and 0s) — produces enormous sequences, which is bad because sequence length is exactly what a fixed context window limits.

2. The fix is to group bits into bytes first (256 possible values), then run **byte-pair encoding (BPE)**: repeatedly find the most frequent adjacent pair of symbols in the training text and merge it into a new single symbol, starting the new symbol IDs at 256 and counting up.

3. Repeating that merge step thousands of times builds a vocabulary of "tokens" that's much more compact than raw bytes but still covers arbitrary text — GPT-4-class tokenizers land around 100k+ symbols this way.

4. A token isn't a word or a fixed unit — it's whatever chunk of text ended up frequent enough in the training corpus to earn its own merged symbol. Common words often become one token; rarer or foreign words fragment into several.

5. Because the vocabulary is learned from a specific training corpus, two different models' tokenizers can (and do) chunk the identical input string differently — there's no canonical tokenization, only "however this model's BPE run happened to merge things."

6. Tokenization is the seam between raw text and everything the model actually reasons over — the model never sees characters, only token IDs, so quirks of tokenization (e.g. how numbers or whitespace get chunked) can leak into odd model behavior (Karpathy calls out things like arithmetic and spelling as places this shows up).

7. Pretraining = take a huge scrape of internet text, tokenize all of it, and train the network to predict the next token given the tokens before it — that's the entire objective, repeated across the whole corpus.

8. Training adjusts the network's weights until its predicted next-token probability distribution matches the statistics of the real training data as closely as possible — it's fitting a probability distribution, not memorizing lookup answers.

9. The result of pretraining alone is a "base model": very good at continuing text in a statistically plausible way, but with no notion of being a helpful assistant — it just completes whatever pattern it's given, which is why raw base models aren't what ships as a chat product.

10. Inference is that same next-token-prediction process run forward at generation time: feed in a starting sequence, sample one new token from the model's output distribution, append it to the sequence, and repeat — the context window grows by one token each step, and because sampling is involved, the exact same prompt won't always produce the exact same continuation.
