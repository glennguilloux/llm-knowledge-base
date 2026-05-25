---
id: "python-patterns-retry-logic"
title: "Retry Logic with Tenacity"
language: "python"
category: "patterns"
subcategory: "resilience"
tags: ["retry", "tenacity", "exponential-backoff", "resilience", "transient"]
version: "3.10+"
retrieval_hint: "retry tenacity exponential backoff resilience transient error"
last_verified: "2026-05-24"
confidence: "high"
---

# Retry Logic with Tenacity

## When to Use
- Handling transient network failures
- Rate-limited API calls
- Database connection retries
- Any operation that may fail temporarily

## Standard Pattern

```python
from tenacity import (
    retry,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
    wait_fixed,
    retry_if_exception_type,
    retry_if_result,
    before_sleep_log,
    RetryError,
)
import logging
import httpx

logger = logging.getLogger(__name__)


# Basic retry with exponential backoff
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def fetch_data(url: str) -> dict:
    """Fetch data with automatic retry on failure."""
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


# Retry on specific exceptions
@retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=1, max=30),
)
def resilient_api_call(url: str) -> dict:
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


# Retry on specific return values
@retry(
    retry=retry_if_result(lambda result: result.get("status") == "pending"),
    stop=stop_after_delay(60),
    wait=wait_fixed(2),
)
def poll_status(task_id: str) -> dict:
    return httpx.get(f"https://api.example.com/tasks/{task_id}").json()


# Retry with both exceptions and return values
@retry(
    retry=(
        retry_if_exception_type(httpx.HTTPStatusError)
        | retry_if_result(lambda r: r.status_code == 429)
    ),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
)
def api_call_with_rate_limit(url: str) -> httpx.Response:
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response
```

## Common Mistakes

```python
# WRONG: Infinite retry loop
while True:
    try:
        result = fetch(url)
        break
    except Exception:
        time.sleep(1)  # Never gives up!

# CORRECT: Use tenacity with max attempts
@retry(stop=stop_after_attempt(3))
def fetch(url):
    return httpx.get(url).json()

# WRONG: Retrying on all exceptions
@retry
def process():
    risky_operation()  # Retries even on programming errors!

# CORRECT: Retry only on transient errors
@retry(retry=retry_if_exception_type((ConnectionError, TimeoutError)))
def process():
    risky_operation()

# WRONG: No backoff between retries
@retry(stop=stop_after_attempt(5), wait=wait_fixed(0))
def api_call():
    return httpx.get(url).json()  # Hammers the server!

# CORRECT: Use exponential backoff
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=30),
)
def api_call():
    return httpx.get(url).json()
```

## Gotchas
- `stop_after_attempt(3)` means 3 total attempts (not 3 retries)
- `wait_exponential(multiplier=1, min=1, max=10)` waits 1s, 2s, 4s, 8s, 10s, 10s...
- Use `retry_if_exception_type()` to only retry on specific exceptions
- `retry_if_result()` retries based on return value (not exceptions)
- Use `|` to combine retry conditions
- `before_sleep_log()` logs each retry attempt
- `RetryError` wraps the last exception when all retries are exhausted

## Related
- python/web/requests/error-handling.md
- python/patterns/error-handling.md
