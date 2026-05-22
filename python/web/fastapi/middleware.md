---
id: "python-web-fastapi-middleware"
title: "Custom Middleware in FastAPI"
language: "python"
category: "web"
subcategory: "middleware"
tags: ["fastapi", "middleware", "request", "response", "logging", "cors"]
version: "3.10+"
retrieval_hint: "FastAPI middleware request response logging CORS timing"
last_verified: "2026-05-22"
confidence: "high"
---

# Custom Middleware in FastAPI

## When to Use
- Request/response logging
- Timing requests
- Adding headers to all responses
- CORS configuration
- Authentication preprocessing

## Standard Pattern

```python
import time
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()
logger = logging.getLogger(__name__)


# CORS middleware (built-in)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom middleware using BaseHTTPMiddleware
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{duration:.4f}"
        logger.info(
            "%s %s completed in %.4fs",
            request.method,
            request.url.path,
            duration,
        )
        return response


app.add_middleware(TimingMiddleware)


# Custom middleware using raw ASGI (more performant)
class RequestIDMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            import uuid
            request_id = str(uuid.uuid4())
            scope["state"] = {"request_id": request_id}
            
            async def send_with_header(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    headers[b"x-request-id"] = request_id.encode()
                    message["headers"] = list(headers.items())
                await send(message)
            
            await self.app(scope, receive, send_with_header)
        else:
            await self.app(scope, receive, send)


# For raw ASGI middleware, use add_middleware differently
# app.add_middleware(RequestIDMiddleware)
```

## Common Mistakes

```python
# WRONG: Modifying request.state in BaseHTTPMiddleware
class BadMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user = get_user(request)  # May not propagate!
        return await call_next(request)

# CORRECT: Use dependencies for request-level state
async def get_current_user(request: Request) -> User:
    return get_user(request)

@app.get("/protected")
async def protected(user: User = Depends(get_current_user)):
    pass

# WRONG: Not awaiting call_next
class BadMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = call_next(request)  # Missing await!
        return response

# CORRECT: Always await call_next
class GoodMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        return response

# WRONG: Catching all exceptions silently
class BadMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            return Response("Error", status_code=500)  # Swallows errors!

# CORRECT: Let exceptions propagate or handle specifically
class GoodMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        return await call_next(request)  # Let FastAPI handle errors
```

## Gotchas
- Middleware runs in LIFO order (last added runs first)
- `BaseHTTPMiddleware` wraps the entire request/response cycle
- Raw ASGI middleware is more performant but more complex
- `request.state` may not persist across middleware (use dependencies instead)
- CORS middleware must be added before routes that need it
- Use `call_next(request)` to pass to the next middleware/route
- Middleware affects ALL routes — use dependencies for route-specific logic

## Related
- python/web/fastapi/auth-jwt.md
- python/web/fastapi/error-handling.md
- python/web/fastapi/basics.md
