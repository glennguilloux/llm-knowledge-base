---
id: "python-web-requests-auth"
title: "HTTP Authentication with requests"
language: "python"
category: "web"
subcategory: "authentication"
tags: ["requests", "authentication", "basic", "bearer", "oauth", "api-key"]
version: "3.10+"
retrieval_hint: "requests authentication basic bearer OAuth API key header"
last_verified: "2026-05-22"
confidence: "high"
---

# HTTP Authentication with requests

## When to Use
- Authenticating with REST APIs
- Using Basic auth, Bearer tokens, or API keys
- OAuth2 flows
- Custom authentication headers

## Standard Pattern

```python
import requests
from requests.auth import HTTPBasicAuth


# Basic Authentication
def basic_auth(url: str, username: str, password: str) -> requests.Response:
    return requests.get(url, auth=HTTPBasicAuth(username, password), timeout=10)

# Shortcut for Basic auth
def basic_auth_shortcut(url: str, username: str, password: str) -> requests.Response:
    return requests.get(url, auth=(username, password), timeout=10)


# Bearer Token (OAuth2)
def bearer_auth(url: str, token: str) -> requests.Response:
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers, timeout=10)


# API Key in header
def api_key_auth(url: str, api_key: str) -> requests.Response:
    headers = {"X-API-Key": api_key}
    return requests.get(url, headers=headers, timeout=10)


# API Key in query parameter
def api_key_query(url: str, api_key: str) -> requests.Response:
    params = {"api_key": api_key}
    return requests.get(url, params=params, timeout=10)


# Session with persistent auth
def authenticated_session(token: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


# Usage
session = authenticated_session("my-token")
response = session.get("https://api.example.com/data")
```

## Common Mistakes

```python
# WRONG: Hardcoding credentials
requests.get(url, auth=("admin", "password123"))  # Credentials in source!

# CORRECT: Use environment variables
import os
username = os.environ["API_USERNAME"]
password = os.environ["API_PASSWORD"]
requests.get(url, auth=(username, password), timeout=10)

# WRONG: Sending token in body instead of header
requests.post(url, json={"token": "my-token"})  # Not standard!

# CORRECT: Use Authorization header
requests.get(url, headers={"Authorization": "Bearer my-token"}, timeout=10)

# WRONG: Not using HTTPS for auth
requests.get("http://api.example.com/login", auth=("user", "pass"))  # Credentials in plain text!

# CORRECT: Always use HTTPS for authentication
requests.get("https://api.example.com/login", auth=("user", "pass"), timeout=10)
```

## Gotchas
- Basic auth sends credentials as base64 (not encrypted) — always use HTTPS
- Bearer tokens go in `Authorization: Bearer <token>` header
- API keys can go in headers, query params, or cookies — check the API docs
- Use `requests.Session()` for persistent auth across multiple requests
- `auth=` parameter is only for Basic auth; other auth goes in `headers=`
- OAuth2 flows require additional libraries (`requests-oauthlib`, `authlib`)
- Never log or print authentication credentials

## Related
- python/web/requests/basics.md
- python/web/requests/sessions.md
- crypto/jwt-tokens.md
