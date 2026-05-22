---
id: "python-web-fastapi-basics"
title: "FastAPI Application Setup and Routing"
language: "python"
category: "web"
subcategory: "api-framework"
tags: ["fastapi", "routing", "api", "rest", "uvicorn", "pydantic"]
version: "3.10+"
retrieval_hint: "FastAPI app setup routing endpoint REST API uvicorn"
last_verified: "2026-05-22"
confidence: "high"
---

# FastAPI Application Setup and Routing

## When to Use
- Building REST APIs
- Creating microservices
- Prototyping APIs quickly with auto-generated docs
- Building async web services

## Standard Pattern

```python
from fastapi import FastAPI, HTTPException, Query, Path, Depends
from pydantic import BaseModel, Field

app = FastAPI(title="My API", version="1.0.0")


# Request/response models
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    age: int = Field(..., ge=0, le=150)


class UserResponse(BaseModel):
    id: int
    name: str
    email: str


# In-memory storage (use a database in production)
users: dict[int, dict] = {}
next_id = 1


# Routes
@app.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
) -> list[dict]:
    """List all users with pagination."""
    all_users = list(users.values())
    return all_users[skip : skip + limit]


@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate) -> dict:
    """Create a new user."""
    global next_id
    user_data = {"id": next_id, **user.model_dump()}
    users[next_id] = user_data
    next_id += 1
    return user_data


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int = Path(..., gt=0)) -> dict:
    """Get a user by ID."""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    return users[user_id]


@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int = Path(..., gt=0)) -> None:
    """Delete a user."""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    del users[user_id]


# Run with: uvicorn main:app --reload
```

## Common Mistakes

```python
# WRONG: Using sync function for I/O-bound work
@app.get("/data")
def get_data():
    result = requests.get("https://api.example.com")  # Blocks event loop!
    return result.json()

# CORRECT: Use async with httpx/aiohttp
@app.get("/data")
async def get_data():
    async with httpx.AsyncClient() as client:
        result = await client.get("https://api.example.com")
    return result.json()

# WRONG: Not using Pydantic for request validation
@app.post("/users")
async def create_user(name: str, email: str):  # No validation!
    return {"name": name, "email": email}

# CORRECT: Use Pydantic models
@app.post("/users")
async def create_user(user: UserCreate):  # Automatic validation
    return user

# WRONG: Returning raw dicts without response_model
@app.get("/users/{id}")
async def get_user(id: int):
    return users[id]  # No schema validation, no docs

# CORRECT: Use response_model for schema
@app.get("/users/{id}", response_model=UserResponse)
async def get_user(id: int):
    return users[id]
```

## Gotchas
- FastAPI is async by default; use `def` for sync endpoints, `async def` for async
- Use `Path()`, `Query()`, `Body()` for parameter validation and documentation
- `response_model` validates output and filters extra fields
- `status_code=201` for POST creating resources
- Use `Depends()` for dependency injection (DB connections, auth)
- Auto-generated docs at `/docs` (Swagger) and `/redoc` (ReDoc)
- Use `HTTPException` for error responses, not raw `Response`

## Real-World Example

### REST API with CRUD, Validation, and Error Handling

```python
from typing import Annotated
from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field

app = FastAPI()


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    quantity: int = Field(..., ge=0)


class ItemResponse(ItemCreate):
    id: int

    class Config:
        from_attributes = True


# Simulated database
items_db: dict[int, dict] = {}
next_id = 1


@app.get("/items", response_model=list[ItemResponse])
async def list_items(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    all_items = list(items_db.values())
    return all_items[skip : skip + limit]


@app.post("/items", response_model=ItemResponse, status_code=201)
async def create_item(item: ItemCreate):
    global next_id
    record = {"id": next_id, **item.model_dump()}
    items_db[next_id] = record
    next_id += 1
    return record


@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: Annotated[int, Path(ge=1)]):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return items_db[item_id]


@app.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: Annotated[int, Path(ge=1)]):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    del items_db[item_id]
```

## Related
- python/web/fastapi/auth-jwt.md
- python/web/fastapi/request-validation.md
- python/web/fastapi/error-handling.md
- python/data/pydantic-v2/models.md
