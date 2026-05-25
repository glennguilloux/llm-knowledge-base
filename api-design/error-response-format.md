---
id: "api-design-error-response-format"
title: "Standard Error Response Format for REST APIs"
language: "multi"
category: "api-design"
tags: ["api-design", "errors", "error-handling", "rest", "http"]
version: "n/a"
retrieval_hint: "error response format REST API error handling standards"
last_verified: "2026-05-24"
confidence: "high"
---

# Standard Error Response Format for REST APIs

## When to Use
- Designing error responses for a REST API
- Standardizing error handling across API endpoints
- Building client-friendly error messages
- Implementing consistent error reporting for debugging

## Standard Pattern

```python
from typing import Any
from dataclasses import dataclass, field
from flask import jsonify


# === Standard Error Envelope ===
@dataclass
class ApiError:
    code: str  # Machine-readable error code
    message: str  # Human-readable summary
    details: list[dict] = field(default_factory=list)  # Per-field errors
    request_id: str | None = None  # For correlating with logs


def error_response(
    status: int,
    code: str,
    message: str,
    details: list[dict] | None = None,
    request_id: str | None = None,
) -> tuple:
    """Return a standardized JSON error response."""
    body = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details:
        body["error"]["details"] = details
    if request_id:
        body["error"]["request_id"] = request_id

    return jsonify(body), status


# === Usage Examples ===

# Validation error
@app.route("/api/users", methods=["POST"])
def create_user():
    errors = validate_user(request.json)
    if errors:
        return error_response(
            status=422,
            code="VALIDATION_ERROR",
            message="Invalid input",
            details=[
                {"field": "email", "message": "Invalid email format"},
                {"field": "age", "message": "Must be at least 18"},
            ],
        )

# Authentication error
@app.route("/api/protected")
@auth_required
def protected():
    if not current_user:
        return error_response(
            status=401,
            code="UNAUTHORIZED",
            message="Authentication required",
        )

# Not found
@app.route("/api/users/<int:user_id>")
def get_user(user_id):
    user = find_user(user_id)
    if not user:
        return error_response(
            status=404,
            code="NOT_FOUND",
            message=f"User {user_id} not found",
        )


# === HTTP Status Code Mapping ===
# 400 Bad Request     — malformed input, invalid JSON
# 401 Unauthorized    — missing or invalid authentication
# 403 Forbidden       — authenticated but not authorized
# 404 Not Found       — resource doesn't exist
# 409 Conflict        — duplicate resource, version conflict
# 422 Unprocessable   — validation failure
# 429 Too Many Req    — rate limited
# 500 Internal Error  — unexpected server error
```

## Common Mistakes

```python
# WRONG: Inconsistent error shapes across endpoints
# /api/users returns: {"error": "User not found"}
# /api/orders returns: {"message": "Order not found"}
# /api/products returns: {"errors": ["Product not found"]}

# CORRECT: Standardized envelope everywhere
{"error": {"code": "NOT_FOUND", "message": "User not found"}}


# WRONG: Leaking internal details in production
{"error": {"message": "KeyError: 'name' at line 42 in users.py"}}

# CORRECT: Safe, user-facing messages
{"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}}
# Internal details go in logs, not the response


# WRONG: Returning 200 with an error body
@app.route("/api/users/<int:user_id>")
def get_user(user_id):
    user = find_user(user_id)
    if not user:
        return {"status": "error", "message": "Not found"}  # Still 200 OK!

# CORRECT: Use appropriate HTTP status codes
@app.route("/api/users/<int:user_id>")
def get_user(user_id):
    user = find_user(user_id)
    if not user:
        return error_response(404, "NOT_FOUND", f"User {user_id} not found")


# WRONG: Missing error code (message-only is hard to handle programmatically)
{"error": {"message": "Invalid input"}}

# CORRECT: Include machine-readable code
{"error": {"code": "VALIDATION_ERROR", "message": "Invalid input", "details": [...]}}


# WRONG: Generic message without details for validation
{"error": {"code": "VALIDATION_ERROR", "message": "Invalid input"}}
# Client doesn't know which field is wrong

# CORRECT: Include per-field details
{"error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
        {"field": "email", "message": "Invalid email format"}
    ]
}}
```

## Gotchas
- **Consistency is king**: Every error response must have the same shape. Inconsistency forces clients to write per-endpoint error handling.
- **Error codes vs HTTP status**: Use both. HTTP status gives the broad category (4xx vs 5xx). Error codes give the specific problem (VALIDATION_ERROR vs RATE_LIMITED).
- **Don't expose stack traces**: Never include stack traces, file paths, or internal identifiers in production error responses. Log them server-side.
- **PII in error messages**: Be careful not to leak personal information in error messages (e.g., "User john@example.com not found" reveals the email exists).
- **Validation detail format**: Per-field errors should consistently include `field` and `message`. Optionally include `code` for programmatic handling.
- **Rate limiting headers**: On 429 responses, include `Retry-After` header and a clear message so clients can self-throttle.
- **Request ID tracing**: Include a `request_id` in error responses to correlate with server logs for debugging.

## Related
- rest-conventions.md
- api-design/pagination-patterns.md
