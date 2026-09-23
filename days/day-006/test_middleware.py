"""Day 6: verify LoggingMiddleware logs one row per /chat call.

Both the LLM client and the Postgres insert are mocked (same trick as Day
3's test for the token source) - this test needs neither a live LLM key nor
a live Postgres to run.
"""

import importlib.util
from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

# Day 3 also has an app.py with a test that does `import app`. Since both
# live in sibling directories with no __init__.py, a bare `import app` here
# would collide in sys.modules with whichever one pytest imported first when
# running the whole days/ tree together - loading this file's app.py under a
# private module name sidesteps that regardless of run order.
_spec = importlib.util.spec_from_file_location(
    "day006_app", Path(__file__).resolve().parent / "app.py"
)
app_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(app_module)


async def fake_tokens(prompt: str) -> AsyncIterator[str]:
    for word in ["pong", " ", "pong"]:
        yield word


@pytest.mark.asyncio
async def test_middleware_logs_one_row_with_mocked_source_and_db(monkeypatch):
    monkeypatch.setitem(app_module.TOKEN_SOURCES, "ollama", fake_tokens)

    mock_insert = AsyncMock()
    monkeypatch.setattr(app_module, "insert_request", mock_insert)

    transport = ASGITransport(app=app_module.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream(
            "GET", "/chat", params={"prompt": "Reply with exactly one word: pong"}
        ) as response:
            assert response.headers["content-type"].startswith("text/event-stream")
            async for _ in response.aiter_lines():
                pass  # drain the stream so the middleware sees the final body chunk

    mock_insert.assert_awaited_once()
    kwargs = mock_insert.call_args.kwargs
    assert kwargs["provider"] == "ollama"
    assert kwargs["model"] == app_module.OLLAMA_MODEL
    assert kwargs["prompt_tokens"] > 0
    assert kwargs["completion_tokens"] == len(app_module.ENCODING.encode("pong pong"))
    assert kwargs["ttfb_ms"] >= 0
    assert kwargs["latency_ms"] >= kwargs["ttfb_ms"]
    assert kwargs["cost_usd"] == 0.0  # llama3.2:3b isn't in Day 5's pricing table


@pytest.mark.asyncio
async def test_middleware_skips_logging_on_bad_provider(monkeypatch):
    mock_insert = AsyncMock()
    monkeypatch.setattr(app_module, "insert_request", mock_insert)

    transport = ASGITransport(app=app_module.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/chat", params={"prompt": "hi", "provider": "nonexistent"})

    assert response.status_code == 400
    mock_insert.assert_not_awaited()
