---
id: "python-stdlib-concurrency-choices"
title: "Concurrency: Threading vs Multiprocessing vs asyncio"
language: "python"
category: "stdlib"
tags: ["concurrency", "threading", "multiprocessing", "asyncio", "parallelism", "gil"]
version: "3.10+"
retrieval_hint: "threading multiprocessing asyncio GIL concurrency parallelism"
last_verified: "2026-05-24"
confidence: "high"
---

# Concurrency: Threading vs Multiprocessing vs asyncio

## When to Use
- Choosing the right concurrency model for your workload
- I/O-bound vs CPU-bound performance optimization
- Understanding Python's GIL limitations
- Building concurrent network services

## Standard Pattern

```python
# asyncio — best for I/O-bound (network, database, file)
# Single-threaded, cooperative multitasking, no race conditions
import asyncio
import httpx

async def fetch_url(client: httpx.AsyncClient, url: str) -> str:
    response = await client.get(url)
    return response.text

async def fetch_all(urls: list[str]) -> list[str]:
    async with httpx.AsyncClient() as client:
        tasks = [fetch_url(client, url) for url in urls]
        return await asyncio.gather(*tasks)

# Use when: HTTP requests, database queries, WebSocket, file I/O

# threading — best for I/O-bound with blocking libraries
# Shared memory, GIL limits CPU parallelism
from concurrent.futures import ThreadPoolExecutor
import requests

def fetch_url(url: str) -> str:
    return requests.get(url).text  # Blocking call

def fetch_all(urls: list[str]) -> list[str]:
    with ThreadPoolExecutor(max_workers=10) as executor:
        return list(executor.map(fetch_url, urls))

# Use when: library is blocking (requests, psycopg2), legacy code integration

# multiprocessing — best for CPU-bound work
# Separate processes, bypasses GIL, higher overhead
from concurrent.futures import ProcessPoolExecutor
import math

def heavy_computation(n: int) -> float:
    return sum(math.sin(i) * math.cos(i) for i in range(n))

def compute_all(numbers: list[int]) -> list[float]:
    with ProcessPoolExecutor() as executor:
        return list(executor.map(heavy_computation, numbers))

# Use when: CPU-intensive calculations, data processing, image processing

# ProcessPoolExecutor for CPU-bound
from multiprocessing import Pool

def process_chunk(data: list[dict]) -> list[dict]:
    return [transform(item) for item in data]

def parallel_process(data: list[dict], chunks: int = 4) -> list[dict]:
    chunk_size = len(data) // chunks
    chunks_list = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    with Pool(processes=chunks) as pool:
        results = pool.map(process_chunk, chunks_list)
    return [item for chunk in results for item in chunk]
```

## Common Mistakes

```python
# WRONG: Using threading for CPU-bound work
from threading import Thread

def cpu_work():
    # Heavy computation — GIL prevents parallel execution
    return sum(i * i for i in range(10_000_000))

threads = [Thread(target=cpu_work) for _ in range(4)]
# NOT faster than single thread — GIL blocks parallelism

# CORRECT: Use multiprocessing for CPU-bound
from multiprocessing import Pool
with Pool(4) as p:
    results = p.map(cpu_work, [None] * 4)  # Actually parallel

# WRONG: Using asyncio for CPU-bound work
async def cpu_work():
    return sum(i * i for i in range(10_000_000))  # Blocks event loop!

# CORRECT: Run CPU-bound in executor
async def cpu_work():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: sum(i * i for i in range(10_000_000)))

# WRONG: Race condition with shared state
from threading import Thread
counter = 0

def increment():
    global counter
    for _ in range(100_000):
        counter += 1  # NOT atomic — race condition!

# CORRECT: Use Lock or atomic operations
import threading
counter = 0
lock = threading.Lock()

def increment():
    global counter
    for _ in range(100_000):
        with lock:
            counter += 1

# WRONG: Mixing blocking and async code
async def fetch():
    result = requests.get("https://api.example.com")  # Blocks event loop!

# CORRECT: Use async HTTP library
async def fetch():
    async with httpx.AsyncClient() as client:
        result = await client.get("https://api.example.com")
```

## Gotchas
- Python's GIL prevents true parallel execution of Python bytecode in threads
- threading: good for I/O wait, bad for CPU — GIL releases during I/O operations
- multiprocessing: true parallelism but higher memory overhead (separate process per worker)
- asyncio: lowest overhead for I/O, but ALL libraries must be async-compatible
- `asyncio.gather()` runs coroutines concurrently, not in parallel (single thread)
- `ProcessPoolExecutor` pickles arguments and results — functions and lambdas can't be pickled
- Threading has race conditions — use `Lock`, `Queue`, or `threading.local`
- `multiprocessing.Queue` is process-safe, `queue.Queue` is thread-safe
- Context switch overhead makes threading slower than asyncio for many small I/O tasks

## Related
- python/stdlib/asyncio-basics.md
- python/stdlib/httpx.md
- go/concurrency/patterns.md
