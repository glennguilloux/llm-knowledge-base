---
id: "python-web-requests-basics"
title: "HTTP Requests with requests Library"
language: "python"
category: "web"
subcategory: "http-client"
tags: ["requests", "http", "get", "post", "api", "rest"]
version: "3.10+"
retrieval_hint: "HTTP GET POST requests API call REST client"
last_verified: "2026-05-24"
confidence: "high"
---

# HTTP Requests with requests Library

## When to Use
- Calling REST APIs
- Downloading web resources
- Interacting with third-party services
- Quick HTTP debugging and prototyping

## Standard Pattern

```python
import requests
from requests.exceptions import RequestException, Timeout, HTTPError


def get_json(url: str, params: dict | None = None, timeout: int = 10) -> dict:
    """Make a GET request and return JSON response."""
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Timeout:
        raise RequestException(f"Request to {url} timed out after {timeout}s")
    except HTTPError as e:
        raise RequestException(f"HTTP {e.response.status_code}: {e}")


def post_json(url: str, data: dict, headers: dict | None = None, timeout: int = 10) -> dict:
    """POST JSON data and return response."""
    response = requests.post(
        url,
        json=data,
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def put_json(url: str, data: dict, timeout: int = 10) -> dict:
    """PUT JSON data and return response."""
    response = requests.put(url, json=data, timeout=timeout)
    response.raise_for_status()
    return response.json()


def delete(url: str, timeout: int = 10) -> bool:
    """DELETE request, returns True if successful."""
    response = requests.delete(url, timeout=timeout)
    response.raise_for_status()
    return True


# Usage
data = get_json("https://api.example.com/users")
result = post_json("https://api.example.com/users", {"name": "Alice"})
```

## Common Mistakes

```python
# WRONG: No timeout — can hang forever
requests.get("https://api.example.com/data")

# CORRECT: Always set a timeout
requests.get("https://api.example.com/data", timeout=10)

# WRONG: Using data= for JSON payload
requests.post(url, data={"key": "value"})  # Sends as form-encoded

# CORRECT: Use json= for JSON payload
requests.post(url, json={"key": "value"})  # Sends as application/json

# WRONG: Not checking response status
response = requests.get(url)
data = response.json()  # May fail if status is 4xx/5xx

# CORRECT: Check status first
response = requests.get(url, timeout=10)
response.raise_for_status()  # Raises HTTPError for 4xx/5xx
data = response.json()

# WRONG: Ignoring timeout tuple
requests.get(url, timeout=10)  # Same timeout for connect and read

# CORRECT: Separate connect and read timeouts
requests.get(url, timeout=(3, 10))  # 3s connect, 10s read
```

## Gotchas
- `response.json()` raises `requests.exceptions.JSONDecodeError` on invalid JSON
- Use `response.raise_for_status()` to catch HTTP errors early
- The `timeout` parameter is `(connect_timeout, read_timeout)` as a tuple
- `response.text` returns decoded string, `response.content` returns raw bytes
- Use `requests.Session()` for connection pooling and cookie persistence
- `response.status_code` is available even without `raise_for_status()`
- Redirects are followed by default; use `allow_redirects=False` to disable

## Related
- python/web/requests/auth.md
- python/web/requests/sessions.md
- python/web/requests/error-handling.md
