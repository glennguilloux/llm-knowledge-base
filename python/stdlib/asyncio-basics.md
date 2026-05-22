---
id: "python-stdlib-asyncio-basics"
title: "Async/Await Patterns with asyncio"
language: "python"
category: "stdlib"
subcategory: "concurrency"
tags: ["asyncio", "async", "await", "concurrency", "coroutine"]
version: "3.10+"
retrieval_hint: "async await concurrency coroutine gather task"
last_verified: "2026-05-22"
confidence: "high"
---

# Async/Await Patterns with asyncio

## When to Use
- I/O-bound concurrency (HTTP requests, database queries, file I/O)
- Handling many simultaneous connections (web servers, chat bots)
- Non-blocking operations in async frameworks (FastAPI, aiohttp)

## Standard Pattern

```python
import asyncio
import aiohttp


async def fetch_url(session: aiohttp.ClientSession, url: str) -> str:
    """Fetch a single URL asynchronously."""
    async with session.get(url) as response:
        return await response.text()


async def fetch_multiple(urls: list[str]) -> list[str]:
    """Fetch multiple URLs concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)


async def main() -> None:
    urls = [
        "https://httpbin.org/get",
        "https://httpbin.org/ip",
        "https://httpbin.org/headers",
    ]
    results = await fetch_multiple(urls)
    for url, result in zip(urls, results):
        print(f"{url}: {len(result)} bytes")


# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
```

## Common Mistakes

```python
# WRONG: Forgetting await
async def get_data():
    result = fetch_data()  # Returns coroutine, not result!
    print(result)           # <coroutine object fetch_data at 0x...>

# CORRECT: Always await coroutines
async def get_data():
    result = await fetch_data()
    print(result)           # Actual data

# WRONG: Using time.sleep in async code
async def slow():
    time.sleep(5)  # Blocks entire event loop!

# CORRECT: Use asyncio.sleep
async def slow():
    await asyncio.sleep(5)  # Non-blocking

# WRONG: Creating tasks without gathering
async def bad():
    asyncio.create_task(work())  # Task may not complete before function returns

# CORRECT: Gather or await tasks
async def good():
    task = asyncio.create_task(work())
    await task  # Wait for completion
```

## Gotchas
- `asyncio.run()` creates a new event loop; don't call it inside an existing loop
- Use `asyncio.gather()` for concurrent execution, `asyncio.create_task()` for fire-and-forget
- `asyncio.gather()` returns results in the same order as input tasks
- Use `asyncio.TaskGroup` (Python 3.11+) for structured concurrency with better error handling
- Never mix blocking I/O (`requests`, `open()`) with async code without `run_in_executor()`
- `await` can only be used inside `async def` functions
- Use `aiohttp` or `httpx` for async HTTP, not `requests`

## Real-World Example

### Concurrent API Calls with Timeout and Error Aggregation

```python
import asyncio
import httpx
from dataclasses import dataclass


@dataclass
class ServiceResult:
    service: str
    data: dict | None = None
    error: str | None = None


async def fetch_with_timeout(client: httpx.AsyncClient, url: str, timeout: float = 5.0) -> dict:
    response = await asyncio.wait_for(client.get(url), timeout=timeout)
    response.raise_for_status()
    return response.json()


async def fetch_all(services: dict[str, str]) -> list[ServiceResult]:
    async with httpx.AsyncClient() as client:
        tasks = {
            name: asyncio.create_task(
                fetch_with_timeout(client, url),
                name=name,
            )
            for name, url in services.items()
        }
        results = []
        for name, task in tasks.items():
            try:
                data = await task
                results.append(ServiceResult(service=name, data=data))
            except asyncio.TimeoutError:
                results.append(ServiceResult(service=name, error="timeout"))
            except httpx.HTTPStatusError as e:
                results.append(ServiceResult(service=name, error=f"HTTP {e.response.status_code}"))
            except Exception as e:
                results.append(ServiceResult(service=name, error=str(e)))
        return results


async def main():
    services = {
        "users": "https://api.example.com/users",
        "orders": "https://api.example.com/orders",
        "inventory": "https://api.example.com/inventory",
    }
    results = await fetch_all(services)
    for r in results:
        status = "OK" if r.data else f"FAIL: {r.error}"
        print(f"  {r.service}: {status}")
    return results


if __name__ == "__main__":
    asyncio.run(main())
```

## Related
- python/web/fastapi/basics.md
- python/patterns/retry-logic.md
