---
id: "python-stdlib-httpx"
title: "HTTP Client with httpx"
language: "python"
category: "stdlib"
tags: ["httpx", "http", "client", "async", "requests", "api"]
version: "3.10+"
retrieval_hint: "httpx HTTP client async requests timeout retry session"
last_verified: "2026-05-22"
confidence: "high"
---

# HTTP Client with httpx

## When to Use
- Making HTTP requests to external APIs
- Need async HTTP support (with FastAPI, asyncio)
- Need HTTP/2 support
- Replacing `requests` with a modern alternative

## Standard Pattern

```python
import httpx

# Simple GET request
response = httpx.get("https://api.example.com/users")
print(response.status_code)
print(response.json())

# POST with JSON body
response = httpx.post(
    "https://api.example.com/users",
    json={"name": "Alice", "email": "alice@example.com"},
    headers={"Authorization": "Bearer token123"},
)

# With timeout
response = httpx.get(
    "https://api.example.com/slow",
    timeout=httpx.Timeout(10.0, connect=5.0),
)

# Using a client (connection pooling, persistent settings)
with httpx.Client(
    base_url="https://api.example.com",
    timeout=10.0,
    headers={"Authorization": "Bearer token123"},
) as client:
    users = client.get("/users").json()
    user = client.get("/users/1").json()
    result = client.post("/users", json={"name": "Bob"})

# Async usage
async def fetch_users():
    async with httpx.AsyncClient(
        base_url="https://api.example.com",
        timeout=10.0,
    ) as client:
        response = await client.get("/users")
        return response.json()

# Retry with transport
transport = httpx.HTTPTransport(retries=3)
with httpx.Client(transport=transport) as client:
    response = client.get("https://api.example.com/data")

# Streaming large responses
with httpx.stream("GET", "https://example.com/large-file") as response:
    with open("output.bin", "wb") as f:
        for chunk in response.iter_bytes(chunk_size=8192):
            f.write(chunk)

# File upload
with open("document.pdf", "rb") as f:
    response = httpx.post(
        "https://api.example.com/upload",
        files={"file": ("document.pdf", f, "application/pdf")},
    )

# Error handling
response = httpx.get("https://api.example.com/data")
response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx
```

## Common Mistakes

```python
# WRONG: Creating a new client per request (no connection pooling)
for url in urls:
    response = httpx.get(url)  # New TCP connection each time

# CORRECT: Reuse client
with httpx.Client() as client:
    for url in urls:
        response = client.get(url)

# WRONG: No timeout (may hang forever)
response = httpx.get("https://api.example.com")  # No timeout!

# CORRECT: Always set timeout
response = httpx.get("https://api.example.com", timeout=10.0)

# WRONG: Using requests in async code
async def fetch():
    return requests.get("https://api.example.com")  # Blocks event loop!

# CORRECT: Use httpx.AsyncClient
async def fetch():
    async with httpx.AsyncClient() as client:
        return await client.get("https://api.example.com")

# WRONG: Not raising on HTTP errors
response = httpx.get("https://api.example.com/missing")
data = response.json()  # May fail — response is 404 HTML

# CORRECT: Check status
response = httpx.get("https://api.example.com/missing")
response.raise_for_status()
data = response.json()

# WRONG: AsyncClient outside context manager
client = httpx.AsyncClient()
await client.get("https://api.example.com")  # Connection leak!

# CORRECT: Use async with
async with httpx.AsyncClient() as client:
    await client.get("https://api.example.com")
```

## Gotchas
- `httpx` API is very similar to `requests` — migration is straightforward
- `httpx.Client` (sync) and `httpx.AsyncClient` (async) manage connection pools
- Default timeout is 5 seconds — set explicitly for production code
- `response.json()` raises on invalid JSON — wrap in try/except if uncertain
- `httpx.stream()` is for large responses — don't load 1GB into memory
- AsyncClient must be used with `async with` — without it, connections leak
- `httpx` supports HTTP/2 — pass `http2=True` to Client
- `raise_for_status()` raises `HTTPStatusError` with response details
- File uploads use `files` parameter, not `json` — multipart/form-data encoding

## Related
- python/stdlib/asyncio-basics.md
- python/web/fastapi/basics.md
- python/patterns/retry-logic.md
