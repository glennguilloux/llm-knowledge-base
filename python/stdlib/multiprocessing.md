---
id: "python-stdlib-multiprocessing"
title: "Multiprocessing vs Threading vs asyncio"
language: "python"
category: "concurrency"
tags: ["multiprocessing", "threading", "asyncio", "concurrency", "parallelism", "GIL", "process-pool"]
version: "3.10+"
retrieval_hint: "multiprocessing threading asyncio concurrency parallelism GIL process pool thread pool"
last_verified: "2026-05-22"
confidence: "high"
---

# Multiprocessing vs Threading vs asyncio

## When to Use
- **multiprocessing**: CPU-bound work (math, image processing, data crunching) — bypasses the GIL
- **threading**: I/O-bound work with blocking libraries (requests, file I/O) — shares memory
- **asyncio**: I/O-bound work with async libraries (httpx, aiohttp, asyncpg) — single-threaded, cooperative

## Standard Pattern

```python
import asyncio
import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


# --- CPU-bound: Use multiprocessing ---
def compute_heavy(n: int) -> int:
    """CPU-intensive computation."""
    total = 0
    for i in range(n):
        total += i * i
    return total


def run_cpu_parallel(numbers: list[int]) -> list[int]:
    """Run CPU-bound tasks in parallel processes."""
    with ProcessPoolExecutor() as pool:
        results = list(pool.map(compute_heavy, numbers))
    return results


# --- I/O-bound blocking: Use threading ---
def fetch_url_blocking(url: str) -> str:
    """Blocking I/O operation."""
    import httpx

    response = httpx.get(url, timeout=10)
    return response.text[:100]


def run_io_threaded(urls: list[str]) -> list[str]:
    """Run blocking I/O in threads."""
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(fetch_url_blocking, urls))
    return results


# --- I/O-bound async: Use asyncio ---
async def fetch_url_async(url: str) -> str:
    """Non-blocking I/O operation."""
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10)
        return response.text[:100]


async def run_io_async(urls: list[str]) -> list[str]:
    """Run async I/O concurrently."""
    tasks = [fetch_url_async(url) for url in urls]
    return await asyncio.gather(*tasks)


# --- Shared state between processes ---
def worker_with_shared_value(shared_value: multiprocessing.Value, lock: multiprocessing.Lock) -> None:
    """Worker that modifies shared state safely."""
    for _ in range(100):
        with lock:
            shared_value.value += 1


def run_shared_state() -> int:
    """Demonstrate shared state between processes."""
    shared = multiprocessing.Value("i", 0)
    lock = multiprocessing.Lock()

    processes = [
        multiprocessing.Process(target=worker_with_shared_value, args=(shared, lock))
        for _ in range(4)
    ]

    for p in processes:
        p.start()
    for p in processes:
        p.join()

    return shared.value  # 400


# --- Combining async with thread pool for blocking code ---
async def run_blocking_in_thread(func, *args):
    """Run a blocking function in a thread pool from async code."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)
```

## Common Mistakes

```python
# WRONG: Using multiprocessing for I/O-bound work
with ProcessPoolExecutor() as pool:
    results = list(pool.map(fetch_url, urls))  # Overhead of process creation for I/O!

# CORRECT: Use threading for blocking I/O
with ThreadPoolExecutor(max_workers=10) as pool:
    results = list(pool.map(fetch_url, urls))

# WRONG: Using threading for CPU-bound work (GIL prevents parallelism)
with ThreadPoolExecutor() as pool:
    results = list(pool.map(compute_heavy, numbers))  # Still sequential due to GIL!

# CORRECT: Use multiprocessing for CPU-bound work
with ProcessPoolExecutor() as pool:
    results = list(pool.map(compute_heavy, numbers))

# WRONG: Using time.sleep() in asyncio code
async def bad():
    time.sleep(5)  # Blocks entire event loop!

# CORRECT: Use asyncio.sleep()
async def good():
    await asyncio.sleep(5)

# WRONG: Not handling process pool shutdown
pool = ProcessPoolExecutor()
results = pool.map(func, data)  # Pool may not clean up on error

# CORRECT: Use context manager
with ProcessPoolExecutor() as pool:
    results = list(pool.map(func, data))

# WRONG: Sharing mutable state between processes without synchronization
shared_list = []  # Each process has its own copy!

# CORRECT: Use multiprocessing.Manager for shared state
with multiprocessing.Manager() as manager:
    shared_list = manager.list()
```

## Gotchas
- The GIL prevents true parallel execution of Python bytecode in threads — use multiprocessing for CPU-bound work
- `ProcessPoolExecutor` has significant overhead per task — batch work into larger chunks for best performance
- `ThreadPoolExecutor` is ideal for I/O-bound work that uses blocking libraries (requests, open(), boto3)
- `asyncio` is the most efficient for high-concurrency I/O but requires async-compatible libraries
- Multiprocessing requires picklable functions and arguments — lambdas and closures don't work
- Use `if __name__ == "__main__":` guard when using multiprocessing to avoid infinite process spawning on Windows
- `multiprocessing.Queue` is process-safe; `queue.Queue` is thread-safe but not process-safe

## Related
- python/stdlib/asyncio-basics.md
- python/stdlib/httpx.md
