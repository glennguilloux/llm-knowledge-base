---
id: "python-concurrency-asyncio-basics"
title: "asyncio Event Loop and Task Patterns"
language: "python"
category: "concurrency"
subcategory: "asyncio"
tags: ["asyncio", "async", "await", "event-loop", "task", "gather", "semaphore"]
version: "3.10+"
retrieval_hint: "asyncio event loop task gather semaphore timeout concurrent async await"
last_verified: "2026-05-22"
confidence: "high"
---

# asyncio Event Loop and Task Patterns

## When to Use
- I/O-bound concurrency: HTTP requests, database queries, file operations
- Managing many simultaneous connections (web servers, chat, WebSocket)
- Coordinating multiple async operations (parallel API calls)
- Rate-limiting concurrent operations with semaphores

## Standard Pattern

```python
import asyncio
from asyncio import Semaphore, TaskGroup
from collections.abc import Coroutine
from typing import Any


# --- Basic async/await ---
async def fetch_url(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()


# --- Run multiple tasks concurrently ---
async def fetch_all(urls: list[str]) -> list[dict]:
    tasks = [fetch_url(url) for url in urls]
    return await asyncio.gather(*tasks)


# --- With error handling ---
async def fetch_all_safe(urls: list[str]) -> list[dict | Exception]:
    tasks = [fetch_url(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results  # Each element is either dict or Exception


# --- TaskGroup (Python 3.11+) ---
async def fetch_with_taskgroup(urls: list[str]) -> list[dict]:
    results = []
    async with TaskGroup() as tg:
        tasks = [tg.create_task(fetch_url(url)) for url in urls]
    return [task.result() for task in tasks]


# --- Semaphore for rate limiting ---
async def fetch_limited(urls: list[str], max_concurrent: int = 5) -> list[dict]:
    sem = Semaphore(max_concurrent)

    async def limited_fetch(url: str) -> dict:
        async with sem:
            return await fetch_url(url)

    return await asyncio.gather(*[limited_fetch(url) for url in urls])


# --- Timeout ---
async def fetch_with_timeout(url: str, timeout: float = 10.0) -> dict:
    try:
        return await asyncio.wait_for(fetch_url(url), timeout=timeout)
    except asyncio.TimeoutError:
        return {"error": "timeout"}


# --- Background tasks ---
async def background_worker(queue: asyncio.Queue) -> None:
    while True:
        item = await queue.get()
        if item is None:  # Poison pill
            break
        try:
            await process_item(item)
        finally:
            queue.task_done()


async def main():
    queue: asyncio.Queue[dict] = asyncio.Queue()

    # Start workers
    workers = [asyncio.create_task(background_worker(queue)) for _ in range(3)]

    # Enqueue work
    for item in data:
        await queue.put(item)

    # Wait for completion
    await queue.join()

    # Stop workers
    for _ in workers:
        await queue.put(None)
    await asyncio.gather(*workers)


# --- Run from sync code ---
result = asyncio.run(fetch_url("https://api.example.com"))
```

## Common Mistakes

```python
# WRONG: Calling async function without await
async def main():
    fetch_url("https://example.com")  # Creates coroutine but never runs it!

# CORRECT: Always await async calls
async def main():
    result = await fetch_url("https://example.com")

# WRONG: Blocking the event loop
async def fetch_data():
    time.sleep(5)  # Blocks entire event loop!
    return await get_data()

# CORRECT: Use asyncio.sleep for async delays
async def fetch_data():
    await asyncio.sleep(5)  # Non-blocking
    return await get_data()

# WRONG: Creating tasks without keeping references
async def main():
    asyncio.create_task(background_work())  # May be garbage collected!

# CORRECT: Store task references
async def main():
    task = asyncio.create_task(background_work())
    try:
        await task
    except asyncio.CancelledError:
        pass

# WRONG: Using gather without return_exceptions
results = await asyncio.gather(*tasks)  # First exception kills all tasks

# CORRECT: Handle exceptions gracefully
results = await asyncio.gather(*tasks, return_exceptions=True)
for result in results:
    if isinstance(result, Exception):
        log_error(result)
```

## Gotchas
- `asyncio.run()` creates a new event loop — don't call it inside an already-running loop
- `asyncio.create_task()` schedules immediately; `await` is not needed to start it
- `gather()` returns results in the same order as inputs, not completion order
- Use `asyncio.as_completed()` for processing results as they arrive
- `TaskGroup` (3.11+) cancels all tasks if any raises an exception
- `Semaphore` is not re-entrant — don't acquire the same semaphore twice in one task
- `wait_for()` cancels the task on timeout — handle `CancelledError` for cleanup
- `Queue` is the async equivalent of `queue.Queue` — use for producer/consumer patterns

## Related
- python/concurrency/celery-basics.md
- python/stdlib/httpx.md
- python/web/fastapi/basics.md
