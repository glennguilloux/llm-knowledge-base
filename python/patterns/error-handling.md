---
id: "python-patterns-error-handling"
title: "Exception Handling Patterns"
language: "python"
category: "patterns"
subcategory: "error-handling"
tags: ["exception", "error", "try-except", "custom-exception", "hierarchy"]
version: "3.10+"
retrieval_hint: "exception error try-except custom exception hierarchy"
last_verified: "2026-05-22"
confidence: "high"
---

# Exception Handling Patterns

## When to Use
- Defining custom exception hierarchies
- Structured error handling in applications
- API error responses
- Graceful degradation

## Standard Pattern

```python
# Custom exception hierarchy
class AppError(Exception):
    """Base exception for the application."""
    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class NotFoundError(AppError):
    """Resource not found."""
    def __init__(self, resource: str, identifier: str | int) -> None:
        super().__init__(
            message=f"{resource} with id '{identifier}' not found",
            code="NOT_FOUND",
        )
        self.resource = resource
        self.identifier = identifier


class ValidationError(AppError):
    """Input validation failed."""
    def __init__(self, field: str, message: str) -> None:
        super().__init__(
            message=f"Validation error on '{field}': {message}",
            code="VALIDATION_ERROR",
        )
        self.field = field


class ConflictError(AppError):
    """Resource conflict (duplicate, etc.)."""
    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="CONFLICT")


# Structured error handling
def process_order(order_id: int) -> dict:
    """Process an order with proper error handling."""
    try:
        order = get_order(order_id)
    except NotFoundError:
        raise
    except Exception as e:
        raise AppError(f"Failed to retrieve order: {e}") from e

    try:
        validate_order(order)
    except ValidationError:
        raise

    try:
        result = execute_order(order)
    except Exception as e:
        raise AppError(f"Order execution failed: {e}") from e

    return result


# Context manager for error wrapping
from contextlib import contextmanager
from typing import Generator


@contextmanager
def error_context(operation: str) -> Generator[None, None, None]:
    """Wrap exceptions with context."""
    try:
        yield
    except AppError:
        raise
    except Exception as e:
        raise AppError(f"Error during {operation}: {e}") from e


# Usage
with error_context("user creation"):
    create_user(data)
```

## Common Mistakes

```python
# WRONG: Catching bare Exception
try:
    process()
except Exception:
    pass  # Swallows all errors!

# CORRECT: Catch specific exceptions
try:
    process()
except NotFoundError:
    raise
except ValidationError as e:
    log.warning(f"Validation failed: {e}")
    raise

# WRONG: Not chaining exceptions
try:
    data = fetch(url)
except ConnectionError:
    raise AppError("Failed to fetch")  # Loses original traceback!

# CORRECT: Use 'from' to chain exceptions
try:
    data = fetch(url)
except ConnectionError as e:
    raise AppError("Failed to fetch") from e

# WRONG: Catching too broadly
try:
    result = complex_operation()
except Exception as e:
    return {"error": str(e)}  # Returns 200 with error body!

# CORRECT: Let exceptions propagate to error handler
result = complex_operation()  # Let FastAPI/Flask handle the exception
```

## Gotchas
- `raise ... from e` preserves the original exception chain
- `except Exception` catches most errors but not `SystemExit`, `KeyboardInterrupt`
- Use `finally` for cleanup that must run regardless of exceptions
- Custom exceptions should inherit from `Exception`, not `BaseException`
- `except (TypeError, ValueError)` catches multiple exception types
- Use `logging.exception()` to log the full traceback
- Consider using `contextlib.suppress()` for expected exceptions

## Real-World Example

### Layered Error Handling: Service → API → Client

```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# --- Domain Layer ---
class AppError(Exception):
    def __init__(self, message: str, code: str, status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: int):
        super().__init__(
            f"{resource} {resource_id} not found",
            code="NOT_FOUND",
            status_code=404,
        )


class ValidationError(AppError):
    def __init__(self, field: str, detail: str):
        super().__init__(
            f"Validation error on '{field}': {detail}",
            code="VALIDATION_ERROR",
            status_code=422,
        )


# --- Service Layer ---
class UserService:
    def __init__(self, db):
        self.db = db

    async def get_user(self, user_id: int) -> dict:
        user = await self.db.fetch_one("SELECT * FROM users WHERE id = :id", {"id": user_id})
        if not user:
            raise NotFoundError("User", user_id)
        return dict(user)

    async def create_user(self, email: str, name: str) -> dict:
        if "@" not in email:
            raise ValidationError("email", "Invalid email format")
        existing = await self.db.fetch_one(
            "SELECT id FROM users WHERE email = :email", {"email": email}
        )
        if existing:
            raise ValidationError("email", "Email already exists")
        user_id = await self.db.execute(
            "INSERT INTO users (email, name) VALUES (:email, :name)",
            {"email": email, "name": name},
        )
        return {"id": user_id, "email": email, "name": name}


# --- API Layer (FastAPI) ---
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    logger.error(f"{exc.code}: {exc.message}", extra={"path": request.url.path})
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "detail": exc.message},
    )


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    service = UserService(db=get_db())
    return await service.get_user(user_id)
```

## Related
- python/web/fastapi/error-handling.md
- python/stdlib/logging.md
