1. Explain in your own words: why does time-to-first-token matter more than total latency for a chat UI, even when total latency is unchanged?

Total latency is what the backend experiences; time-to-first-token (TTFT) is what the user experiences. A person watching a chat UI isn't judging how long the full answer took to generate - they're judging how long they stared at a blank screen before anything happened. Once tokens start appearing, the response *feels* like it's working even if it keeps generating for several more seconds, because there's now visible progress and something to read while the rest streams in.

Two responses with identical total latency can feel completely different depending on how that time is distributed. A 5-second response that shows the first word after 200ms feels fast and responsive - like a normal conversation with pauses to think mid-sentence. A 5-second response that shows nothing for 4.5 seconds and then dumps the whole answer at once feels broken or frozen, because the user has no signal that anything is happening and starts wondering if the request even went through.

This is exactly why day-003's endpoint streams over SSE instead of waiting for Ollama's full response and returning it in one shot: the total time to generate the answer is the same either way, but streaming turns that same latency budget into something that reads as immediate and alive instead of a stall.

2. What breaks if: you never call is_disconnected(), and a user closes the tab three seconds into a long generation - what keeps running, and who pays for it?

Nothing on the server side notices the tab closed, so nothing stops. The generator keeps calling into the httpx stream, Ollama keeps producing tokens, and the FastAPI task keeps looping and yielding SSE chunks - into a socket that no longer has anyone listening. The request just runs to completion as if the user were still there, then quietly discards the output when the final write fails.

Who pays depends on the provider. For local Ollama it's not a dollar cost, but it's still waste: the GPU/CPU keeps grinding on a response nobody will read, which is capacity taken away from any other request that's actually waiting on that same local model. For a paid provider (Gemini, OpenRouter) it's a literal money cost - you're billed for every output token generated after the user left, since the upstream call was never told to stop. At a small scale this is a rounding error; under real traffic, where people abandon chats constantly, it becomes a meaningful chunk of wasted spend and wasted concurrency (each abandoned request holds an open upstream connection and a worker task for however long the full generation takes, instead of freeing up almost immediately).

This is why day-003 doesn't actually rely on is_disconnected() anymore - sse-starlette cancels the generator's asyncio task itself when it detects the client is gone, and catching asyncio.CancelledError around the streaming loop is what lets us actually stop the upstream Ollama/Gemini call at that point instead of letting it run to completion for nothing.

3. What breaks if: you drop the httpx timeout entirely and Ollama silently stops responding mid-request - what happens to the FastAPI worker handling that request?

Because this is async (one event loop multiplexing many coroutines, not one thread per request), a stuck request doesn't freeze the whole server - other requests keep getting scheduled and served normally as long as they don't also depend on the same stalled thing. But the one task handling that request is stuck forever on `await` inside `aiter_lines()`, since there's no timeout to raise `httpx.TimeoutException` and force it to give up.

That stuck task never gets cleaned up on its own: it keeps its open TCP connection to Ollama alive indefinitely, keeps the SSE response to the client open (the browser just spins forever), and keeps its memory (buffers, the Request/Response objects, the task itself) alive for as long as the process runs. If the client eventually gives up and closes the tab, our CancelledError handling would catch that and clean it up - but if the client also just sits there waiting, or if this happens repeatedly across many requests, these hung connections pile up with nothing to reap them.

At scale that's a slow resource leak, not a crash: each hang permanently consumes a file descriptor, a connection slot against Ollama, and a bit of memory. Enough of them over time and you exhaust the connection pool or the process's file descriptor limit, and the server stops being able to open new connections at all - a self-inflicted denial of service caused entirely by the missing timeout, not by any actual load.

## Recall quiz (10 min)

From Day 2 (first LLM calls, cost/latency comparison):

1. When comparing latency across providers, why is the median of 3 runs a better number to report than a single run?

A single run can get unlucky in either direction - a cold connection, a slow network hop, a busy moment on the provider's servers, a GC pause - and any one of those makes that one number misleading. The median throws out that noise: it's not swayed by one outlier run the way an average would be, so it reflects the "typical" latency you'd actually expect rather than whatever happened to occur on one attempt.

2. A provider charges $1 per million input tokens and $5 per million output tokens. A call uses 500 input tokens and 200 output tokens. What's the cost?

Input: 500 / 1,000,000 x $1 = $0.0005
Output: 200 / 1,000,000 x $5 = $0.001
Total: $0.0015

3. Ollama showed near-zero network overhead compared to Gemini and OpenRouter in your Day 2 run. Does that prove Ollama's underlying model is computationally faster? Why or why not?

No. What was measured is end-to-end latency, not raw model compute time - and network round-trip is only one piece of that. Ollama skips the network hop entirely (it's on the same machine), which alone would make it look faster even if its actual token-generation speed were identical to or slower than Gemini/OpenRouter's. It's also a single small local model running on this machine's hardware, being compared against different, larger models running on someone else's GPUs - not a controlled comparison of the same workload on the same hardware. To actually claim one model computes faster, you'd need to isolate pure inference time (excluding network) and hold the hardware and model size roughly constant.

4. If max_tokens is set far higher than what the model actually generates, are you billed for the unused budget?

No. max_tokens is a ceiling on generation, not a pre-purchased block - you're billed for output tokens actually produced, not for the gap between what was generated and what was allowed. Setting it to 4000 for a response that naturally stops at 20 tokens costs the same as if you'd set max_tokens=20, aside from it being a slightly looser safety rail that could let a runaway generation go further (and cost more) than a tighter limit would.
