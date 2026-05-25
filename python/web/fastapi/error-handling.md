---
id: "python-web-fastapi-error-handling"
title: "Error Handling in FastAPI"
language: "python"
category: "web"
subcategory: "error-handling"
tags: ["fastapi", "error", "exception", "http", "validation"]
version: "3.10+"
retrieval_hint: "FastAPI error handling HTTPException validation error response"
last_verified: "2026-05-24"
confidence: "high"
---

# Error Handling in FastAPI

## When to Use
- Returning structured error responses
- Handling validation errors gracefully
- Custom exception handlers
- Consistent error format across API

## Standard Pattern

```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

app = FastAPI()


# Standard error response model
class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None


# Custom exception
class NotFoundError(HTTPException):
    def __init__(self, resource: str, resource_id: int | str) -> None:
        super().__init__(
            status_code=404,
            detail=f"{resource} with id {resource_id} not found",
        )


class ConflictError(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=409, detail=detail)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Format Pydantic validation errors as clean JSON."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": errors},
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": exc.detail or "Resource not found"},
    )


# Usage
@app.get("/items/{item_id}")
async def get_item(item_id: int) -> dict:
    if item_id > 100:
        raise NotFoundError("Item", item_id)
    return {"id": item_id, "name": f"Item {item_id}"}


@app.post("/items")
async def create_item(item: dict) -> dict:
    if item.get("name") == "duplicate":
        raise ConflictError("Item with this name already exists")
    return item
```

## Common Mistakes

```python
# WRONG: Returning generic 500 for all errors
@app.get("/items/{id}")
async def get_item(id: int):
    try:
        return db.get(id)
    except Exception:
        return {"error": "Something went wrong"}  # 200 with error body!

# CORRECT: Use HTTPException with proper status codes
@app.get("/items/{id}")
async def get_item(id: int):
    item = db.get(id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# WRONG: Catching and re-raising without context
@app.get("/items/{id}")
async def get_item(id: int):
    try:
        return db.get(id)
    except Exception:
        raise  # Loses HTTP context

# CORRECT: Let FastAPI handle unhandled exceptions (returns 500)
# Or use custom exception handlers for specific cases

# WRONG: Using detail=None
raise HTTPException(status_code=400, detail=None)  # Null in response

# CORRECT: Always provide a detail string
raise HTTPException(status_code=400, detail="Invalid request parameters")
```

## Gotchas
- FastAPI returns `{"detail": "..."}` for HTTPException by default
- Pydantic validation errors return 422 with detailed error list
- Use `status_code=` in decorator to set default success status
- Custom exception handlers override default behavior
- `RequestValidationError` catches Pydantic/validation errors
- Unhandled exceptions return 500 with `{"detail": "Internal Server Error"}`
- Use `JSONResponse` for custom responses, not raw `Response`

## Related
- python/web/fastapi/basics.md
- python/web/fastapi/request-validation.md
- python/patterns/error-handling.md
