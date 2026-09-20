"""Day 3: stream a chat reply over Server-Sent Events, backed by a local Ollama
model (Day 2's caller) - no API key, no per-token cost.
"""

import json
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse

load_dotenv()

app = FastAPI()

OLLAMA_HOST = os.getenv("OLLAMA_HOST") or "http://localhost:11434"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
REQUEST_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0)


async def ollama_stream(prompt: str, request: Request):
    """Yield SSE chunks as Ollama streams the response token-by-token."""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_HOST}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": True},
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if await request.is_disconnected():
                        break
                    if not line:
                        continue

                    chunk = json.loads(line)
                    if chunk.get("response"):
                        yield {"event": "message", "data": chunk["response"]}
                    if chunk.get("done"):
                        break
    except httpx.TimeoutException:
        yield {"event": "error", "data": "upstream Ollama request timed out"}
        return


@app.get("/chat", response_class=EventSourceResponse)
async def chat(prompt: str, request: Request):
    return EventSourceResponse(ollama_stream(prompt, request))
