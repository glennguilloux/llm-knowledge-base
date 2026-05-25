---
id: "python-web-requests-sessions"
title: "HTTP Sessions with requests.Session"
language: "python"
category: "web"
subcategory: "http-client"
tags: ["requests", "session", "cookies", "connection-pool", "persistent"]
version: "3.10+"
retrieval_hint: "requests session cookies connection pool persistent"
last_verified: "2026-05-24"
confidence: "high"
---

# HTTP Sessions with requests.Session

## When to Use
- Making multiple requests to the same host (connection pooling)
- Maintaining cookies across requests (login sessions)
- Setting default headers for all requests
- Reusing authentication across requests

## Standard Pattern

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session(
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    timeout: int = 10,
) -> requests.Session:
    """Create a session with retry logic and connection pooling."""
    session = requests.Session()
    
    # Retry strategy
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST", "PUT", "DELETE"],
    )
    
    # Mount adapter with retry strategy
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=10,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Default headers
    session.headers.update({
        "User-Agent": "MyApp/1.0",
        "Accept": "application/json",
    })
    
    return session


# Usage
session = create_session()

# Cookies are automatically persisted
session.post("https://api.example.com/login", json={"user": "alice", "pass": "secret"})
response = session.get("https://api.example.com/profile")  # Cookies sent automatically

# Default headers apply to all requests
response = session.get("https://api.example.com/data")  # Has User-Agent and Accept
```

## Common Mistakes

```python
# WRONG: Creating new session per request
for url in urls:
    session = requests.Session()  # No connection pooling!
    session.get(url)

# CORRECT: Reuse session
session = requests.Session()
for url in urls:
    session.get(url)

# WRONG: Not closing session
session = requests.Session()
response = session.get(url)
# Connection pool not released!

# CORRECT: Use context manager
with requests.Session() as session:
    response = session.get(url)
# Session automatically closed

# WRONG: Setting headers per request
for url in urls:
    requests.get(url, headers={"Authorization": "Bearer token"})  # Repetitive

# CORRECT: Set default headers on session
session = requests.Session()
session.headers.update({"Authorization": "Bearer token"})
for url in urls:
    session.get(url)
```

## Gotchas
- `Session` persists cookies, headers, and connection pool across requests
- Use `session.close()` or `with` statement to release connections
- `HTTPAdapter` configures retry and connection pooling
- `pool_connections` = number of connection pools (per host)
- `pool_maxsize` = max connections per pool
- Cookies from `Set-Cookie` headers are automatically stored and sent
- Use `session.auth = ("user", "pass")` for default auth

## Related
- python/web/requests/basics.md
- python/web/requests/auth.md
- python/web/requests/error-handling.md
