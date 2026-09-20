"""Day 3: verify /chat streams SSE chunks.

Runs against a local Ollama instance (free, no API key) - never a paid API.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app import app


@pytest.mark.asyncio
async def test_chat_streams_sse_from_ollama():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream(
            "GET", "/chat", params={"prompt": "Reply with exactly one word: pong"}
        ) as response:
            assert response.headers["content-type"].startswith("text/event-stream")

            data_chunks = []
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data_chunks.append(line)
                    break

            assert len(data_chunks) >= 1
