---
id: "api-design-rest-conventions"
title: "REST API Design Conventions"
language: "multi"
category: "api-design"
tags: ["api", "rest", "http", "conventions", "pagination", "versioning"]
version: "n/a"
retrieval_hint: "REST API design conventions pagination error response versioning rate limiting"
last_verified: "2026-05-22"
confidence: "high"
---

# REST API Design Conventions

## When to Use
- Designing new REST APIs
- Standardizing existing API responses
- Implementing pagination, filtering, and sorting
- Versioning APIs

## Standard Pattern

```json
// === Resource Naming ===
// Nouns, not verbs. Plural. Nested for relationships.
// GET    /api/v1/users              — list users
// GET    /api/v1/users/42           — get user 42
// POST   /api/v1/users              — create user
// PUT    /api/v1/users/42           — replace user 42
// PATCH  /api/v1/users/42           — partial update
// DELETE /api/v1/users/42           — delete user 42
// GET    /api/v1/users/42/orders    — user's orders

// === Standard Response Envelope ===
// Success:
{
  "data": { "id": 42, "name": "Alice" },
  "meta": { "request_id": "abc-123" }
}

// Collection with pagination:
{
  "data": [
    { "id": 1, "name": "Alice" },
    { "id": 2, "name": "Bob" }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "total_pages": 8
  }
}

// Error:
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      { "field": "email", "message": "Invalid email format" }
    ]
  }
}

// === HTTP Status Codes ===
// 200 OK              — successful GET, PUT, PATCH
// 201 Created         — successful POST (include Location header)
// 204 No Content      — successful DELETE
// 400 Bad Request     — validation error, malformed input
// 401 Unauthorized    — missing or invalid authentication
// 403 Forbidden       — authenticated but not authorized
// 404 Not Found       — resource doesn't exist
// 409 Conflict        — duplicate resource, version conflict
// 422 Unprocessable   — semantic validation error
// 429 Too Many Reqs   — rate limited (include Retry-After header)
// 500 Internal Error  — server bug (don't leak details)
```

```python
# === Pagination Patterns ===

# Offset-based (simple, but unstable on insertions/deletions)
# GET /api/users?page=2&per_page=20
def paginate_offset(page: int, per_page: int):
    offset = (page - 1) * per_page
    items = db.query("SELECT * FROM users ORDER BY id LIMIT %s OFFSET %s", (per_page, offset))
    total = db.query("SELECT COUNT(*) FROM users")
    return {
        "data": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        }
    }

# Cursor-based (stable, preferred for real-time data)
# GET /api/users?cursor=eyJpZCI6NDJ9&limit=20
def paginate_cursor(cursor: str | None, limit: int):
    if cursor:
        cursor_data = decode_cursor(cursor)  # {"id": 42}
        items = db.query(
            "SELECT * FROM users WHERE id > %s ORDER BY id LIMIT %s",
            (cursor_data["id"], limit + 1)
        )
    else:
        items = db.query("SELECT * FROM users ORDER BY id LIMIT %s", (limit + 1,))

    has_next = len(items) > limit
    items = items[:limit]
    next_cursor = encode_cursor({"id": items[-1]["id"]}) if has_next else None
    return {"data": items, "next_cursor": next_cursor, "has_more": has_next}
```

```python
# === Versioning ===
# URL path versioning (most common)
# GET /api/v1/users
# GET /api/v2/users

# Header versioning
# Accept: application/vnd.myapp.v2+json

# === Rate Limiting Headers ===
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 95
# X-RateLimit-Reset: 1640000000
# Retry-After: 60  (on 429 response)
```

## Common Mistakes

```python
# WRONG: Verbs in URLs
POST /api/createUser
GET /api/getUsers
DELETE /api/deleteUser/42

# CORRECT: Nouns + HTTP methods
POST /api/users
GET /api/users
DELETE /api/users/42

# WRONG: Inconsistent error responses
# Some endpoints return: {"error": "msg"}
# Others return: {"message": "msg"}
# Others return: {"errors": ["msg"]}

# CORRECT: Standardized error envelope everywhere

# WRONG: Returning 200 for errors
return {"status": "error", "message": "Not found"}  # Still 200 OK

# CORRECT: Use appropriate HTTP status codes
raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND"}})

# WRONG: GET with request body
GET /api/users/search
{ "name": "Alice", "age_min": 25 }  # Not standard, ignored by many proxies

# CORRECT: Use query parameters or POST for complex searches
GET /api/users?name=Alice&age_min=25
POST /api/users/search  # For complex queries

# WRONG: Not handling CORS
# Frontend can't call API from different origin

# CORRECT: Configure CORS headers
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
```

## Gotchas
- Use plural nouns for resources (`/users` not `/user`) — consistency matters
- `PATCH` for partial updates, `PUT` for full replacement — don't mix them up
- Cursor-based pagination is stable under concurrent inserts/deletes; offset-based is not
- Always return `Content-Type: application/json` — don't let the client guess
- `201 Created` should include a `Location` header pointing to the new resource
- Rate limiting headers let clients self-throttle before hitting 429
- `401 Unauthorized` means "not authenticated"; `403 Forbidden` means "not authorized"
- API versioning in the URL path (`/v1/`) is the simplest and most visible approach
- `OPTIONS` preflight requests are sent by browsers for CORS — handle them
- Pagination `per_page` should have a maximum (e.g., 100) to prevent abuse

## Related
- security/web-security-basics.md
- error-handling/structured-errors.md
- performance/caching-strategies.md
