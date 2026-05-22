---
id: "python-web-fastapi-request-validation"
title: "Request Validation with Pydantic in FastAPI"
language: "python"
category: "web"
subcategory: "validation"
tags: ["fastapi", "pydantic", "validation", "request", "body", "query"]
version: "3.10+"
retrieval_hint: "FastAPI request validation Pydantic body query parameter"
last_verified: "2026-05-22"
confidence: "high"
---

# Request Validation with Pydantic in FastAPI

## When to Use
- Validating API request bodies
- Defining query parameter constraints
- Custom validation logic
- Documenting API schemas automatically

## Standard Pattern

```python
from fastapi import FastAPI, Query, Path, Body, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime

app = FastAPI()


# Request body models
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    price: float = Field(..., gt=0, description="Price must be positive")
    quantity: int = Field(1, ge=0, le=10000)
    tags: list[str] = Field(default_factory=list, max_length=10)
    
    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Name cannot be blank")
        return stripped


class ItemUpdate(BaseModel):
    """All fields optional for PATCH requests."""
    name: str | None = Field(None, min_length=1, max_length=100)
    price: float | None = Field(None, gt=0)
    quantity: int | None = Field(None, ge=0, le=10000)


# Query parameters with validation
@app.get("/items")
async def list_items(
    skip: int = Query(0, ge=0, description="Items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max items to return"),
    search: str | None = Query(None, min_length=1, max_length=100),
    sort_by: str = Query("created_at", pattern=r"^(name|price|created_at)$"),
) -> dict:
    return {"skip": skip, "limit": limit, "search": search, "sort_by": sort_by}


# Path parameters with validation
@app.get("/items/{item_id}")
async def get_item(item_id: int = Path(..., gt=0, description="Item ID")) -> dict:
    return {"item_id": item_id}


# Body with multiple models
@app.post("/items")
async def create_item(item: ItemCreate) -> dict:
    return item.model_dump()


@app.patch("/items/{item_id}")
async def update_item(
    item_id: int = Path(..., gt=0),
    item: ItemUpdate = Body(...),
) -> dict:
    return {"item_id": item_id, **item.model_dump(exclude_unset=True)}
```

## Common Mistakes

```python
# WRONG: No validation on query parameters
@app.get("/items")
async def list_items(skip: int, limit: int):  # No bounds!
    pass

# CORRECT: Use Query() for validation
@app.get("/items")
async def list_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    pass

# WRONG: Using Body() for simple types
@app.post("/items")
async def create_item(name: str = Body()):  # Confusing for clients

# CORRECT: Use Pydantic model for complex bodies
@app.post("/items")
async def create_item(item: ItemCreate):
    pass

# WRONG: Not using exclude_unset for PATCH
@app.patch("/items/{id}")
async def update_item(id: int, item: ItemUpdate):
    update_data = item.model_dump()  # Includes None for unset fields!
    
# CORRECT: Use exclude_unset for PATCH
@app.patch("/items/{id}")
async def update_item(id: int, item: ItemUpdate):
    update_data = item.model_dump(exclude_unset=True)  # Only includes set fields
```

## Gotchas
- `Field(...)` means required; `Field(default=None)` means optional
- `Query()`, `Path()`, `Body()` are for parameter metadata, not Pydantic fields
- Use `Body(embed=True)` when expecting JSON body as `{"field_name": value}`
- `model_dump(exclude_unset=True)` only includes fields explicitly sent by client
- Use `description=` for auto-generated API docs
- `pattern=` uses regex; `min_length=`/`max_length=` for strings
- Custom validators run before type coercion by default

## Related
- python/data/pydantic-v2/models.md
- python/web/fastapi/error-handling.md
- python/web/fastapi/basics.md
