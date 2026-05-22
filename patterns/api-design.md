---
id: "patterns-api-design"
title: "REST API Design Conventions"
language: "multi"
category: "patterns"
tags: ["REST", "API", "design", "conventions", "pagination", "versioning", "error-format"]
version: "n/a"
retrieval_hint: "REST API design conventions pagination versioning error response rate limiting HATEOAS"
last_verified: "2026-05-22"
confidence: "high"
---

# REST API Design Conventions

## When to Use
- Designing new REST APIs
- Standardizing error response formats
- Implementing pagination, filtering, and sorting
- Versioning APIs for backward compatibility

## Standard Pattern

```python
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import Generic, TypeVar

app = FastAPI()

T = TypeVar("T")

# --- Standard response envelope ---
class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str = ""

class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    total: int
    page: int
    limit: int
    has_next: bool

# --- Standard error format ---
class ErrorDetail(BaseModel):
    field: str | None = None
    message: str
    code: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: list[ErrorDetail] = []

# --- Pagination ---
@app.get("/users", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at", pattern=r"^[a-z_]+$"),
    order: str = Query("desc", pattern=r"^(asc|desc)$"),
    search: str = Query("", max_length=100),
):
    # Calculate offset
    offset = (page - 1) * limit
    # Query with limit+1 to check has_next
    users = await get_users(offset=offset, limit=limit + 1, sort=sort, order=order, search=search)
    has_next = len(users) > limit
    users = users[:limit]
    total = await count_users(search=search)

    return PaginatedResponse(
        data=users,
        total=total,
        page=page,
        limit=limit,
        has_next=has_next,
    )

# --- API versioning (URL prefix) ---
# /api/v1/users
# /api/v2/users

# --- Standard HTTP status codes ---
# 200 OK — successful GET, PUT, PATCH
# 201 Created — successful POST that creates
# 204 No Content — successful DELETE
# 400 Bad Request — validation error
# 401 Unauthorized — missing/invalid auth
# 403 Forbidden — insufficient permissions
# 404 Not Found — resource doesn't exist
# 409 Conflict — duplicate resource
# 422 Unprocessable Entity — semantic validation error
# 429 Too Many Requests — rate limited
# 500 Internal Server Error — unhandled exception

# --- Filtering ---
@app.get("/products")
async def list_products(
    category: str | None = None,
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    in_stock: bool | None = None,
):
    filters = {}
    if category:
        filters["category"] = category
    if min_price is not None:
        filters["price__gte"] = min_price
    if max_price is not None:
        filters["price__lte"] = max_price
    if in_stock is not None:
        filters["stock__gt"] = 0 if in_stock else None
    return await get_products(filters)
```

## Common Mistakes

```python
# WRONG: Inconsistent error format
@app.get("/users/{id}")
async def get_user(id: int):
    user = await find_user(id)
    if not user:
        return {"error": "not found"}  # Different format each time!

# CORRECT: Consistent error envelope
@app.get("/users/{id}")
async def get_user(id: int):
    user = await find_user(id)
    if not user:
        raise HTTPException(404, detail={"error": "User not found", "code": "NOT_FOUND"})

# WRONG: Returning 200 for errors
@app.post("/users")
async def create_user(user: UserCreate):
    if exists(user.email):
        return {"success": False, "error": "Email taken"}  # Still 200!

# CORRECT: Use appropriate HTTP status codes
@app.post("/users", status_code=201)
async def create_user(user: UserCreate):
    if exists(user.email):
        raise HTTPException(409, detail="Email already registered")

# WRONG: No pagination
@app.get("/users")
async def list_users():
    return await get_all_users()  # Returns 1M rows!

# CORRECT: Paginate with cursor or offset
@app.get("/users")
async def list_users(page: int = 1, limit: int = 20):
    return await get_users(offset=(page - 1) * limit, limit=limit)

# WRONG: Exposing internal IDs
{"id": 1, "public_id": "abc123"}  # Sequential IDs leak info

# CORRECT: Use UUIDs for public-facing IDs
{"id": "550e8400-e29b-41d4-a716-446655440000"}

# WRONG: No rate limiting
# Any client can hammer your API

# CORRECT: Rate limit per IP/user
# 100 requests per minute per IP
```

## Gotchas
- Use cursor-based pagination for large datasets — offset pagination becomes slow at high offsets
- `PATCH` for partial updates, `PUT` for full replacement — don't mix them
- Return `201 Created` with `Location` header for POST that creates resources
- API versioning: URL prefix (`/v1/`) is most visible; header versioning is cleaner but harder to test
- `422 Unprocessable Entity` for validation errors; `400 Bad Request` for malformed requests
- Rate limiting headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`) help clients self-regulate
- CORS preflight requests (OPTIONS) must be handled for browser-based API calls

## Related
- python/web/fastapi/basics.md
- python/web/fastapi/request-validation.md
- security/web-security-basics.md
