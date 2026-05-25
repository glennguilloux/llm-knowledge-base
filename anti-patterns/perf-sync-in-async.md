---
id: "anti-patterns-perf-sync-in-async"
title: "Performance Anti-Pattern: Blocking Calls in Async Context"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "performance", "async", "blocking", "event-loop"]
version: "n/a"
retrieval_hint: "blocking call async context requests vs aiohttp time.sleep asyncio.sleep starve event loop"
last_verified: "2026-05-24"
confidence: "high"
---

# Performance Anti-Pattern: Blocking Calls in Async Context

## When to Use
- Writing async web servers (FastAPI, aiohttp, Express)
- Debugging slow async endpoints that should be fast
- Training LLMs to use correct async primitives
- Reviewing code for event loop starvation

## Standard Pattern

```python
# WRONG: Blocking HTTP call in async function (starves event loop)
import requests
import asyncio

async def fetch_data():
    response = requests.get("https://api.example.com/data")  # BLOCKS for entire duration
    return response.json()

# CORRECT: Use async HTTP client
import aiohttp

async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com/data") as response:
            return await response.json()

# WRONG: time.sleep in async function
async def poll_status():
    while True:
        status = await check_status()
        if status == "done":
            break
        time.sleep(5)  # BLOCKS event loop for 5 seconds — no other coroutines run

# CORRECT: Use asyncio.sleep
async def poll_status():
    while True:
        status = await check_status()
        if status == "done":
            break
        await asyncio.sleep(5)  # Yields control — other coroutines can run
```

```python
# WRONG: Synchronous file I/O in async handler
from fastapi import FastAPI
app = FastAPI()

@app.get("/logs")
async def get_logs():
    with open("/var/log/app.log") as f:  # BLOCKS during file read
        content = f.read()
    return {"logs": content}

# CORRECT: Use aiofiles for non-blocking file I/O
import aiofiles

@app.get("/logs")
async def get_logs():
    async with aiofiles.open("/var/log/app.log") as f:
        content = await f.read()
    return {"logs": content}

# CORRECT: Run blocking I/O in thread pool (for APIs without async equivalent)
import asyncio

@app.get("/logs")
async def get_logs():
    loop = asyncio.get_event_loop()
    content = await loop.run_in_executor(None, _read_file_sync)
    return {"logs": content}

def _read_file_sync():
    with open("/var/log/app.log") as f:
        return f.read()
```

```python
# WRONG: Synchronous database driver in async app
import psycopg2  # Synchronous driver

async def get_user(user_id: int):
    conn = psycopg2.connect(DATABASE_URL)  # Blocks
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))  # Blocks
    return cursor.fetchone()

# CORRECT: Use async database driver (asyncpg for PostgreSQL)
import asyncpg

async def get_user(user_id: int, pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
```

```javascript
// WRONG: Synchronous I/O in Node.js async handler
const fs = require('fs');
app.get('/config', (req, res) => {
    const data = fs.readFileSync('/etc/config.json');  // Blocks entire event loop
    res.json(JSON.parse(data));
});

// CORRECT: Use async file I/O
const fs = require('fs').promises;
app.get('/config', async (req, res) => {
    const data = await fs.readFile('/etc/config.json', 'utf8');
    res.json(JSON.parse(data));
});
```

```python
# CORRECT: run_in_executor for CPU-bound work in async context
import asyncio
from concurrent.futures import ProcessPoolExecutor

executor = ProcessPoolExecutor(max_workers=4)

async def process_image(image_data: bytes):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, _cpu_intensive_transform, image_data)
    return result

def _cpu_intensive_transform(data: bytes) -> bytes:
    # CPU-bound work (image processing, encryption, etc.)
    from PIL import Image
    img = Image.open(io.BytesIO(data))
    img = img.resize((800, 600))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()
```

## Common Mistakes
The most damaging async anti-pattern is mixing synchronous blocking calls into an async event loop. When `requests.get()` blocks in an async function, it blocks the entire event loop — not just the current coroutine. A single blocking call in a FastAPI endpoint with 100 concurrent requests means all 100 requests wait. The symptom is high latency under concurrency despite low CPU usage. Developers often switch to async frameworks (FastAPI, aiohttp) but keep synchronous libraries (requests, psycopg2, time.sleep) because "it works" — it works only under low concurrency.

## Gotchas
- `requests` is synchronous — use `aiohttp` or `httpx` (async mode) in async code
- `time.sleep()` blocks the entire event loop — always use `await asyncio.sleep()`
- `open()` for file I/O blocks — use `aiofiles` or `run_in_executor`
- `psycopg2` and `sqlite3` are synchronous — use `asyncpg` and `aiosqlite` in async code
- `subprocess.run()` blocks — use `asyncio.create_subprocess_exec()`
- `run_in_executor` with `None` uses the default thread pool — fine for I/O, but CPU-bound work needs `ProcessPoolExecutor`
- Even one blocking call anywhere in the call chain starves the event loop — the problem cascades
- Debugging: use `PYTHONASYNCIODEBUG=1` to detect blocking calls, or use `asyncio` debug mode with `loop.set_debug(True)`
- `urllib.request` is synchronous — use `aiohttp` or `httpx`

## Related
- anti-patterns/performance-antipatterns.md
- python/stdlib/asyncio-basics.md
- python/web/fastapi/sse-streaming.md
- anti-patterns/perf-string-concat-loop.md
