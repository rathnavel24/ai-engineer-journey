# Day 6

## Setup notes (deviations from the brief)

- **No Docker on this machine.** Used the local Homebrew Postgres install instead (`postgresql@18`, started via `brew services start postgresql@18`). Same end result — a real local Postgres on `5432` — just not containerized. `DATABASE_URL` in `.env` points at it (`postgresql://rathnavel:dev@localhost:5432/aej`); `.env.example` shows the docker-default shape (`postgres:dev@localhost:5432/postgres`) for whoever *does* have Docker.
- **Provider/pricing mismatch.** This app calls Ollama and Gemini (Day 3's providers), but Day 5 only priced `gpt-4o` and `claude-sonnet-5`. Rather than invent Gemini pricing or fake a number, `cost.py`'s `estimate_cost()` returns `0.0` for any model it doesn't recognize — Ollama's `0.0` is genuinely correct (local compute, no bill), Gemini's `0.0` is a flagged "untracked," not a claim it's free. See the docstring in `cost.py`.

## Why not BaseHTTPMiddleware

`BaseHTTPMiddleware` doesn't hand your middleware the raw ASGI messages as they arrive — it runs the downstream app to completion first, collecting its response into a `StreamingResponse`-shaped object, and only then gives your `call_next()` something to work with. On a normal JSON endpoint that's invisible, because the entire body is produced in one shot anyway — there's nothing to buffer that wasn't already "one chunk." But `/chat` is SSE specifically *because* the point is to hand the client each token the instant it's produced, over what might be several seconds. `BaseHTTPMiddleware`'s buffering collapses that into "wait for the whole generation to finish, then deliver everything at once" — which is precisely the failure mode Day 3 was built to avoid (see Day 3's TTFT answer). Time-to-first-token would silently become equal to total latency, and the client-visible behavior would look identical to *not streaming at all*, even though the server-side code still looks like it streams.

Raw ASGI middleware (`async def __call__(self, scope, receive, send)`) sidesteps this because there's no intermediate "Response object" step at all — `send` is the literal function the app below calls for every `http.response.start` / `http.response.body` message, and my `wrapped_send` just timestamps and forwards each one immediately before returning. Nothing is held back waiting for the stream to finish; the only thing I buffer is my *own* private copy (`body_chunks`) for token-counting after the fact — the client already has the real bytes by the time that copy is even used.

## Exercises

**1. Explain in your own words: why does BaseHTTPMiddleware fight you specifically on a streaming SSE endpoint, when it works fine on a normal JSON endpoint?**

Covered above — the short version: BaseHTTPMiddleware buffers the *whole* response before your middleware code ever sees it, because internally it runs the downstream app to completion and hands you a materialized response. A JSON endpoint's body is already "one chunk" by the time it's ready, so buffering it changes nothing observable. An SSE endpoint's entire value proposition is delivering partial output early and often — buffering it means the client waits for the full generation before seeing byte one, silently turning a streaming endpoint into a slow non-streaming one.

**2. Coding task: write the SQL query against your requests table that returns p95 latency_ms grouped by provider.**

```sql
SELECT provider,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95_latency_ms
FROM requests
GROUP BY provider;
```

Verified against the live table (2 real rows from today's manual test):

```
 provider |  p95_latency_ms
----------+-------------------
 ollama   | 4328.900628549854
```

**3. What breaks if: Postgres is down when a /chat request comes in — does the SSE response still stream to the client, or does the whole request fail? Which behavior do you want, and what does your middleware need to do to get it?**

As written, the SSE response still streams to the client in full — the logging insert doesn't happen until *after* `await self.app(scope, receive, wrapped_send)` returns, and by that point every `http.response.*` message has already been forwarded through `send()` to the real client. The DB is only touched once the response is already fully delivered. `insert_request()` (including the lazy `asyncpg.create_pool()` call on first use) is wrapped in `try/except Exception`, so a Postgres outage just prints a "failed to log request" line and the request otherwise completes normally from the client's point of view.

That's the behavior I want: logging is best-effort and strictly downstream of the actual feature. An LLM chat response succeeding or failing should never depend on whether the observability database happens to be up — losing a few rows in `requests` during a Postgres outage is a much smaller problem than an outage in your monitoring stack taking down your product. The middleware has to (a) do the insert *after* the response is already sent, not interleaved with it, and (b) catch broadly enough around the insert that a DB-layer exception can't propagate back up through `__call__` and break the ASGI contract.

**4. What breaks if: you count "prompt tokens" as only the user's raw text, ignoring the system prompt you'll add later — where does that estimate quietly go wrong once you add few-shot examples in Week 2?**

Today it's accidentally correct, because there *is* no system prompt yet — `prompt_tokens` is computed straight from the raw `prompt` query-string value, which today is genuinely the entire input. The problem is that the middleware only ever sees that raw value; it has no visibility into whatever gets prepended to it inside `ollama_tokens`/`gemini_tokens` before the request actually goes upstream. The moment a system prompt gets added there, every request silently starts under-billing itself in the logs — real upstream cost goes up, but the number written to `requests.prompt_tokens` doesn't move, because the middleware is still only counting the piece it was handed at the edge.

It gets meaningfully worse with few-shot examples specifically, because those aren't a fixed handful of tokens like a short system instruction — a few well-chosen examples can easily run into the hundreds of tokens, several times larger than the actual user alert/prompt itself. At that point `prompt_tokens` (and therefore `cost_usd`, and any dashboard or budget alert built on top of this table) isn't just slightly low, it's off by whatever multiple the examples add — a table that looks authoritative while quietly measuring the wrong thing. The fix is that token counting has to happen on the *exact* string handed to the LLM API call, not on the raw user input the middleware can see from the outside — which likely means moving the count inside the token-source functions themselves, or having them report back what they actually sent.

## Recall quiz

**(Day 5) Why can gpt-4o and claude-sonnet-5 report different token counts for the exact same input string?**

Each model's tokenizer vocabulary is the product of running byte-pair encoding over that provider's own training corpus, merging whichever byte/character pairs were most frequent *there*. Different corpora produce different merge lists, so the same input string can legally chunk into different token boundaries under each vocabulary — nothing about the string changed, just which ruler is measuring it.

**(Day 5) Between input and output tokens, which is typically priced higher per token, and why?**

Output. Generating it is inherently sequential — one full forward pass per output token, each conditioned on everything generated before it (autoregressive) — while the entire input prompt gets processed in a single parallel forward pass. A token of output costs meaningfully more compute than a token of input, and pricing reflects that.

**(Day 3) In your SSE generator, what specifically triggers the asyncio.CancelledError you're catching?**

sse-starlette's own internal disconnect listener — it directly consumes the ASGI `http.disconnect` message from `receive()` the moment the client goes away, and in response cancels the `asyncio.Task` running my generator. That cancellation is what raises `CancelledError` inside `sse_stream` at whatever `await` it's currently sitting on.

**(Day 3) Why doesn't request.is_disconnected() fire reliably in your sse_stream generator, per what you found building Day 3?**

Because only one coroutine can ever consume a given ASGI message, and `EventSourceResponse` already has its own task doing exactly that — consuming `http.disconnect` from `receive()` internally to decide when to cancel the generator. By the time my own code calls `request.is_disconnected()`, that message has already been claimed by sse-starlette's listener, so my poll is permanently starved and returns `False` no matter what actually happened on the wire.

## Reflection

Building the middleware was mechanically straightforward once "don't buffer" clicked as "just forward every message through `send` immediately" — the harder part was noticing how many of today's numbers are only correct by coincidence of today's code (no system prompt yet, providers Day 5 never priced), which is exactly the kind of thing a table like `requests` will keep reporting confidently and wrong long after the code around it has moved on.
