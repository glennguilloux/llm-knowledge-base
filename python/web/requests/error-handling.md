---
id: "python-web-requests-error-handling"
title: "HTTP Error Handling with requests"
language: "python"
category: "web"
subcategory: "error-handling"
tags: ["requests", "error", "timeout", "retry", "exception", "http"]
version: "3.10+"
retrieval_hint: "requests error timeout retry exception handling HTTP"
last_verified: "2026-05-22"
confidence: "high"
---

# HTTP Error Handling with requests

## When to Use
- Handling network failures gracefully
- Implementing retry logic for transient errors
- Timeouts and connection errors
- HTTP status code handling

## Standard Pattern

```python
import requests
from requests.exceptions import (
    RequestException,
    Timeout,
    ConnectionError,
    HTTPError,
    RetryError,
)
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_resilient_session(
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    timeout: int = 10,
) -> requests.Session:
    """Create session with retry and timeout defaults."""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST", "PUT", "DELETE"],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


def safe_request(
    method: str,
    url: str,
    timeout: int = 10,
    **kwargs,
) -> requests.Response:
    """Make HTTP request with comprehensive error handling."""
    session = create_resilient_session()
    
    try:
        response = session.request(method, url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response
    except Timeout:
        raise RequestException(f"Request to {url} timed out after {timeout}s")
    except ConnectionError:
        raise RequestException(f"Failed to connect to {url}")
    except HTTPError as e:
        status = e.response.status_code
        if status == 429:
            raise RequestException(f"Rate limited by {url}")
        elif status >= 500:
            raise RequestException(f"Server error {status} from {url}")
        else:
            raise RequestException(f"HTTP {status}: {e.response.text}")
    except RetryError:
        raise RequestException(f"Max retries exceeded for {url}")
    finally:
        session.close()


# Usage
try:
    response = safe_request("GET", "https://api.example.com/data")
    data = response.json()
except RequestException as e:
    print(f"Request failed: {e}")
```

## Common Mistakes

```python
# WRONG: No timeout
response = requests.get(url)  # Can hang forever!

# CORRECT: Always set timeout
response = requests.get(url, timeout=10)

# WRONG: Catching bare Exception
try:
    response = requests.get(url)
except Exception:  # Too broad!
    pass

# CORRECT: Catch specific exceptions
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
except Timeout:
    print("Request timed out")
except HTTPError as e:
    print(f"HTTP error: {e.response.status_code}")
except ConnectionError:
    print("Connection failed")

# WRONG: Ignoring status codes
response = requests.get(url)
data = response.json()  # May fail if status is 4xx/5xx

# CORRECT: Check status first
response = requests.get(url, timeout=10)
response.raise_for_status()
data = response.json()
```

## Gotchas
- `timeout=(connect_timeout, read_timeout)` — separate connect and read timeouts
- `raise_for_status()` raises `HTTPError` for 4xx and 5xx status codes
- `Retry` with `backoff_factor=0.5` waits 0.5s, 1s, 2s between retries
- `status_forcelist` only retries on these status codes (not 4xx client errors)
- `allowed_methods` defaults to only `["GET"]` — add others if needed
- Use `session.close()` or `with` to release connections
- `response.text` decodes automatically; `response.content` is raw bytes

## Related
- python/web/requests/basics.md
- python/web/requests/sessions.md
- python/patterns/retry-logic.md
