---
id: "python-web-fastapi-dependency-injection"
title: "FastAPI Dependency Injection Deep Dive"
language: "python"
category: "web"
subcategory: "api-framework"
tags: ["fastapi", "dependency", "injection", "depends", "yield", "async"]
version: "3.10+"
retrieval_hint: "FastAPI Depends dependency injection yield database session auth"
last_verified: "2026-05-24"
confidence: "high"
---

# FastAPI Dependency Injection Deep Dive

## When to Use
- Sharing database connections, sessions, or HTTP clients across endpoints
- Authentication and authorization checks before handler execution
- Request-scoped resources (transaction per request pattern)
- Reusable validation or filtering logic across multiple routes

## Standard Pattern

```python
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from collections.abc import Generator

app = FastAPI()


# --- Database session with yield (cleanup on request end) ---
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# --- Auth dependency chain ---
async def get_token_header(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    return authorization.removeprefix("Bearer ")


async def get_current_user(token: str = Depends(get_token_header)) -> dict:
    payload = verify_jwt(token)  # your JWT logic
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"id": payload["sub"], "email": payload["email"]}


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# --- Reusable query parameter dependency ---
class PaginationParams:
    def __init__(self, skip: int = 0, limit: int = 20):
        self.skip = max(0, skip)
        self.limit = min(100, max(1, limit))


# --- Usage in routes ---
@app.get("/items")
async def list_items(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return db.query(Item).offset(pagination.skip).limit(pagination.limit).all()


@app.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404)
    db.delete(item)
    return {"deleted": item_id}


# --- Caching dependencies (same instance per request) ---
async def get_loader() -> DataLoader:
    return DataLoader()  # Created once per request, reused across Depends chains
```

## Common Mistakes

```python
# WRONG: Creating a new session per query (no transaction)
@app.get("/items")
async def list_items():
    db = SessionLocal()  # No cleanup, no transaction boundary
    items = db.query(Item).all()
    return items

# CORRECT: Use yield dependency for proper lifecycle
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# WRONG: Putting business logic in dependencies
async def get_user_with_posts(db: Session = Depends(get_db), user_id: int = 0):
    user = db.query(User).filter(User.id == user_id).first()
    user.posts = db.query(Post).filter(Post.author_id == user_id).all()
    return user  # Dependency doing too much

# CORRECT: Dependencies handle infra (auth, db), services handle logic
async def get_current_user(token: str = Depends(get_token_header)) -> dict:
    return verify_jwt(token)  # Just auth

@app.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    return UserService(db).get_user_with_posts(user_id)  # Logic in service

# WRONG: Depends() on a class without __init__ params
@app.get("/items")
async def list_items(pagination: PaginationParams = Depends(PaginationParams)):
    # Verbose and confusing

# CORRECT: Use Depends() without args for classes with __init__ params
@app.get("/items")
async def list_items(pagination: PaginationParams = Depends()):
    # FastAPI calls PaginationParams(skip=..., limit=...) from query params
```

## Gotchas
- `yield` dependencies run cleanup code after the response is sent (like context managers)
- `Depends()` without arguments auto-constructs the class from request params
- Dependencies are cached per-request — same dependency called multiple times creates only one instance
- Use `use_cache=False` on `Depends` to force a new instance each time
- Async dependencies run on the event loop; sync dependencies run in a thread pool
- Dependency chains can be arbitrarily deep — FastAPI resolves them recursively
- `BackgroundTasks` can be injected as a dependency alongside others

## Related
- python/web/fastapi/basics.md
- python/web/fastapi/auth-jwt.md
- python/db/sqlalchemy-2.0/models.md
