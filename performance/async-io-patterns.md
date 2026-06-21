---
id: "performance-async-io-patterns"
title: "Async I/O Patterns"
language: "multi"
category: "performance"
tags: ["async", "io", "nonblocking", "event-loop", "concurrency", "performance", "backpressure"]
version: "n/a"
retrieval_hint: "async IO patterns nonblocking event loop backpressure concurrency performance aiohttp asyncio httpx"
last_verified: "2026-06-20"
confidence: "medium"
---

# Async I/O Patterns

## When to Use
- Serving many concurrent I/O-bound requests with limited threads
- Calling multiple external services without blocking worker threads
- Preventing one slow I/O operation from consuming all concurrency
- Building event-loop based services where blocking calls would stall progress

## Standard Pattern

```python
# === Python asyncio: bounded concurrent I/O ===
import asyncio
import aiohttp

async def fetch_one(session: aiohttp.ClientSession, url: str) -> dict:
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()

async def fetch_many(urls: list[str], limit: int) -> list[dict]:
    timeout = aiohttp.ClientTimeout(total=10)
    connector = aiohttp.TCPConnector(limit=limit)
    semaphore = asyncio.Semaphore(limit)

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        async def guarded(url: str) -> dict:
            async with semaphore:
                return await fetch_one(session, url)

        return await asyncio.gather(*(guarded(url) for url in urls))
```

```python
# === FastAPI: async endpoint without blocking the event loop ===
from fastapi import FastAPI
import httpx

app = FastAPI()

@app.get("/external")
async def external_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.test/data")
        response.raise_for_status()
        return response.json()
```

```typescript
// === Node.js: bounded concurrency with a worker pool ===
async function mapLimited<T, R>(
  items: T[],
  limit: number,
  worker: (item: T) => Promise<R>,
): Promise<R[]> {
  const results: R[] = new Array(items.length);
  let next = 0;

  async function runOne(index: number): Promise<void> {
    while (next < items.length) {
      const current = next++;
      results[current] = await worker(items[current]);
    }
  }

  const workers = Array.from(
    { length: Math.min(limit, items.length) },
    (_, index) => runOne(index),
  );

  await Promise.all(workers);
  return results;
}
```

## Common Mistakes

```python
# WRONG: Blocking the event loop with synchronous I/O
@app.get("/slow")
async def slow_endpoint():
    response = requests.get("https://api.example.test/data")  # Blocks event loop
    return response.json()

# CORRECT: Use an async HTTP client
@app.get("/slow")
async def slow_endpoint():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.test/data")
        response.raise_for_status()
        return response.json()
```

```python
# WRONG: Firing unlimited concurrent requests
async def fetch_all(urls):
    return await asyncio.gather(*(fetch_one(url) for url in urls))

# CORRECT: Bound concurrency to protect downstream services and local resources
async def fetch_all(urls, limit):
    semaphore = asyncio.Semaphore(limit)
    async def guarded(url):
        async with semaphore:
            return await fetch_one(url)
    return await asyncio.gather(*(guarded(url) for url in urls))
```

```typescript
// WRONG: Awaiting each request sequentially when they are independent
for (const url of urls) {
  results.push(await fetchJson(url));
}

// CORRECT: Run independent requests concurrently with a limit
const results = await mapLimited(urls, 8, fetchJson);
```

```python
# WRONG: Mixing CPU-heavy work into async handlers
async def render_report():
    return expensive_cpu_transform(payload)  # Stalls event loop

# CORRECT: Move CPU-heavy work to a worker process or thread pool
from fastapi.concurrency import run_in_threadpool

async def render_report():
    return await run_in_threadpool(expensive_cpu_transform, payload)
```

## Gotchas
- Async I/O helps when work is waiting on network, disk, or other I/O, not when the CPU is the bottleneck
- Unbounded concurrency can overwhelm databases, APIs, and event loops
- Blocking libraries inside async code can stall all tasks sharing the event loop
- Timeouts should be set on client requests so slow dependencies do not hold workers indefinitely
- Backpressure is part of the pattern; a queue without a limit only moves the bottleneck
- Cancellation should be propagated so abandoned requests release downstream connections

## Related
- performance/caching-strategies.md
- performance/connection-pooling.md
- performance/database-optimization.md
