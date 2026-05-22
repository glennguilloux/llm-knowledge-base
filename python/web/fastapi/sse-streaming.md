---
id: "python-web-fastapi-sse-streaming"
title: "FastAPI SSE and Streaming Responses"
language: "python"
category: "web"
subcategory: "api-framework"
tags: ["fastapi", "sse", "streaming", "eventsource", "response", "async"]
version: "3.10+"
retrieval_hint: "FastAPI server-sent events SSE streaming response EventSource async generator"
last_verified: "2026-05-22"
confidence: "high"
---

# FastAPI SSE and Streaming Responses

## When to Use
- Real-time progress updates (file uploads, long-running computations)
- Live data feeds (stock prices, dashboards, notifications)
- Chat or AI token streaming (LLM responses word by word)
- File downloads too large to buffer in memory

## Standard Pattern

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse
from collections.abc import AsyncGenerator
import asyncio
import json

app = FastAPI()


# --- Server-Sent Events (SSE) ---
async def event_generator(user_id: int) -> AsyncGenerator[dict, None]:
    """Yields SSE events until client disconnects."""
    try:
        while True:
            # Check for new data
            data = await fetch_user_notifications(user_id)
            if data:
                yield {"event": "notification", "data": json.dumps(data)}
            await asyncio.sleep(2)  # Poll interval
    except asyncio.CancelledError:
        # Client disconnected — cleanup here
        pass


@app.get("/events/{user_id}")
async def user_events(user_id: int):
    return EventSourceResponse(event_generator(user_id))


# --- SSE with initial connection event ---
async def status_stream() -> AsyncGenerator[dict, None]:
    yield {"event": "connected", "data": json.dumps({"status": "ok"})}
    while True:
        metrics = await collect_system_metrics()
        yield {"event": "metrics", "data": json.dumps(metrics)}
        await asyncio.sleep(5)


@app.get("/status/stream")
async def status_endpoint():
    return EventSourceResponse(status_stream())


# --- Streaming large file download ---
async def file_chunk_generator(file_path: str) -> AsyncGenerator[bytes, None]:
    chunk_size = 8192
    async with aiofiles.open(file_path, "rb") as f:
        while chunk := await f.read(chunk_size):
            yield chunk


@app.get("/download/{file_id}")
async def download_file(file_id: int):
    file_path = await resolve_file_path(file_id)
    return StreamingResponse(
        file_chunk_generator(file_path),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file_path.name}"'},
    )


# --- LLM token streaming ---
async def llm_stream(prompt: str) -> AsyncGenerator[str, None]:
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "https://api.openai.com/v1/chat/completions",
            json={"model": "gpt-4", "messages": [{"role": "user", "content": prompt}], "stream": True},
            headers={"Authorization": f"Bearer {API_KEY}"},
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    chunk = json.loads(line.removeprefix("data: "))
                    token = chunk["choices"][0]["delta"].get("content", "")
                    if token:
                        yield token


@app.post("/chat/stream")
async def chat_stream(request: dict):
    return StreamingResponse(llm_stream(request["prompt"]), media_type="text/plain")
```

## Common Mistakes

```python
# WRONG: Buffering entire response before sending
@app.get("/large-data")
async def get_large_data():
    data = fetch_millions_of_rows()  # Loads everything into memory
    return data  # OOM risk

# CORRECT: Stream data in chunks
@app.get("/large-data")
async def get_large_data():
    async def generate():
        async for chunk in fetch_rows_in_batches(batch_size=1000):
            yield json.dumps(chunk) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")

# WRONG: Forgetting Content-Type for SSE
@app.get("/events")
async def events():
    return StreamingResponse(event_gen())  # Browser won't parse as SSE

# CORRECT: Use EventSourceResponse or set correct media type
@app.get("/events")
async def events():
    return EventSourceResponse(event_gen())  # Proper SSE headers

# WRONG: Not handling client disconnection
async def stream():
    while True:
        yield await get_data()  # Keeps running after client leaves

# CORRECT: Handle CancelledError for cleanup
async def stream():
    try:
        while True:
            yield await get_data()
    except asyncio.CancelledError:
        await cleanup_resources()  # Clean up on disconnect
```

## Gotchas
- `StreamingResponse` requires an async generator for async endpoints; sync generators work but block the event loop
- SSE connections are long-lived — consider connection limits and timeouts
- Browser `EventSource` auto-reconnects; implement `id` fields to track last event
- `sse-starlette` package is needed for proper SSE support (`pip install sse-starlette`)
- For production SSE, use Redis Pub/Sub or a message broker as the event source
- Streaming responses bypass response model validation — validate data before yielding
- Nginx/proxies may buffer streaming responses — configure `proxy_buffering off`

## Related
- python/web/fastapi/basics.md
- python/web/fastapi/background-tasks.md
- python/web/websocket-basics.md
