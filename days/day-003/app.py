"""Day 3: stream a chat reply over Server-Sent Events, from either a local
Ollama model (Day 2's caller) or Gemini - swap via ?provider=ollama|gemini
without touching the SSE/disconnect plumbing itself.
"""

import asyncio
import json
import os
from collections.abc import AsyncIterator

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai
from sse_starlette.sse import EventSourceResponse

load_dotenv()

app = FastAPI()

OLLAMA_HOST = os.getenv("OLLAMA_HOST") or "http://localhost:11434"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
REQUEST_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0)


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
