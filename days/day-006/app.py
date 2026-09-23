"""Day 6: Day 3's streaming /chat endpoint, now with request logging.

Every /chat call gets timed (time-to-first-byte, total latency), token-
counted, cost-estimated, and written to Postgres by LoggingMiddleware below -
a raw ASGI middleware, not BaseHTTPMiddleware. See answers.md for why
BaseHTTPMiddleware specifically breaks this endpoint.
"""

import asyncio
import json
import os
import re
import time
from collections.abc import AsyncIterator
from urllib.parse import parse_qs

import httpx
import tiktoken
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai
from sse_starlette.sse import EventSourceResponse

from cost import estimate_cost
from db import insert_request

load_dotenv()

app = FastAPI()

OLLAMA_HOST = os.getenv("OLLAMA_HOST") or "http://localhost:11434"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
REQUEST_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0)

PROVIDER_MODELS = {"ollama": OLLAMA_MODEL, "gemini": GEMINI_MODEL}

# Same encoding Day 5 used as its "exact" case (gpt-4o's o200k_base) - for
# ollama/gemini this is an approximation, same caveat as Day 5's
# claude-sonnet-5 column: labeled as an estimate, not presented as fact.
ENCODING = tiktoken.get_encoding("o200k_base")

# sse-starlette ends lines with \r\n, so the trailing \r must stay out of the capture.
_SSE_DATA_LINE = re.compile(rb"^data:[ ]?(.*?)\r?$", re.MULTILINE)


async def ollama_tokens(prompt: str) -> AsyncIterator[str]:
    """Yield raw text tokens as Ollama streams the response."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        async with client.stream(
            "POST",
            f"{OLLAMA_HOST}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": True},
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue

                chunk = json.loads(line)
                if chunk.get("response"):
                    yield chunk["response"]
                if chunk.get("done"):
                    break


async def gemini_tokens(prompt: str) -> AsyncIterator[str]:
    """Yield raw text tokens as Gemini streams the response."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    client = genai.Client(api_key=api_key)
    stream = await client.aio.models.generate_content_stream(model=GEMINI_MODEL, contents=prompt)
    async for chunk in stream:
        if chunk.text:
            yield chunk.text


TOKEN_SOURCES = {
    "ollama": ollama_tokens,
    "gemini": gemini_tokens,
}


async def sse_stream(token_source: AsyncIterator[str]) -> AsyncIterator[dict]:
    """Wrap any provider's raw-token generator in SSE framing, timeout
    handling, and disconnect logging - this stays provider-agnostic so
    swapping providers never touches it.
    """
    try:
        async for token in token_source:
            yield {"event": "message", "data": token}
    except httpx.TimeoutException:
        yield {"event": "error", "data": "upstream request timed out"}
        return
    except asyncio.CancelledError:
        # sse-starlette cancels this generator's task when it detects the
        # client disconnected - request.is_disconnected() never fires here
        # because sse-starlette's own listener already consumes that ASGI
        # message first.
        print("Client disconnected, stopping stream")
        raise


@app.get("/chat", response_class=EventSourceResponse)
async def chat(prompt: str, provider: str = "ollama"):
    token_source_fn = TOKEN_SOURCES.get(provider)
    if token_source_fn is None:
        raise HTTPException(
            status_code=400,
            detail=f"unknown provider '{provider}', expected one of {list(TOKEN_SOURCES)}",
        )
    return EventSourceResponse(sse_stream(token_source_fn(prompt)))


class LoggingMiddleware:
    """Raw ASGI middleware: times TTFB/total latency and logs one Postgres
    row per /chat call, without ever buffering the streamed response.

    Deliberately not BaseHTTPMiddleware - see answers.md.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] != "/chat":
            return await self.app(scope, receive, send)

        params = parse_qs(scope.get("query_string", b"").decode())
        prompt = params.get("prompt", [""])[0]
        provider = params.get("provider", ["ollama"])[0]

        start = time.perf_counter()
        ttfb = None
        status_code = None
        body_chunks: list[bytes] = []

        async def wrapped_send(message):
            nonlocal ttfb, status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            elif message["type"] == "http.response.body":
                if ttfb is None:
                    ttfb = time.perf_counter() - start
                body_chunks.append(message.get("body", b""))
            await send(message)

        await self.app(scope, receive, wrapped_send)
        latency = time.perf_counter() - start

        if status_code != 200:
            return  # error response (e.g. bad provider) - nothing meaningful to log

        completion_text = "".join(
            m.decode("utf-8", errors="replace")
            for m in _SSE_DATA_LINE.findall(b"".join(body_chunks))
        )
        model = PROVIDER_MODELS.get(provider, provider)
        prompt_tokens = len(ENCODING.encode(prompt))
        completion_tokens = len(ENCODING.encode(completion_text))
        cost_usd = estimate_cost(prompt_tokens, completion_tokens, model)

        try:
            await insert_request(
                provider=provider,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                ttfb_ms=(ttfb or latency) * 1000,
                latency_ms=latency * 1000,
                cost_usd=cost_usd,
            )
        except Exception as exc:
            # Logging must never take down a request that already succeeded.
            print(f"failed to log request to Postgres: {exc}")


app.add_middleware(LoggingMiddleware)
