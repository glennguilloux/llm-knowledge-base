---
id: "python-data-pydantic-v2-models"
title: "Pydantic v2 Data Models"
language: "python"
category: "data"
subcategory: "validation"
tags: ["pydantic", "validation", "model", "serialization", "typing"]
version: "3.10+"
retrieval_hint: "Pydantic model validation serialization BaseModel"
last_verified: "2026-05-22"
confidence: "high"
---

# Pydantic v2 Data Models

## When to Use
- Validating external data (API requests, config files, user input)
- Defining data schemas with type hints
- Serializing/deserializing data (JSON, dict)
- Building settings and configuration objects

## Standard Pattern

```python
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


class UserCreate(BaseModel):
    """Model for creating a user."""
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    age: int = Field(..., ge=0, le=150)
    tags: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        return v.strip()


class UserResponse(BaseModel):
    """Model for API responses (may exclude sensitive fields)."""
    id: int
    name: str
    email: str
    created_at: datetime


class UserUpdate(BaseModel):
    """Model for partial updates (all fields optional)."""
    name: str | None = None
    email: str | None = None
    age: int | None = None


# Usage
user = UserCreate(name="Alice", email="alice@example.com", age=30)

# Serialization
user_dict = user.model_dump()              # Convert to dict
user_json = user.model_dump_json()         # Convert to JSON string

# Deserialization
data = {"name": "Bob", "email": "bob@example.com", "age": 25}
user = UserCreate.model_validate(data)     # From dict
user = UserCreate.model_validate_json('{"name":"Bob","email":"bob@example.com","age":25}')

# Partial validation
user = UserCreate.model_validate(data, strict=False)
```

## Common Mistakes

```python
# WRONG: Using Pydantic v1 syntax
from pydantic import BaseModel

class OldModel(BaseModel):
    class Config:
        orm_mode = True  # Pydantic v1

# CORRECT: Pydantic v2 syntax
from pydantic import ConfigDict

class NewModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# WRONG: Using .dict() and .json() (deprecated in v2)
user.dict()   # Deprecated
user.json()   # Deprecated

# CORRECT: Use model_dump() and model_dump_json()
user.model_dump()
user.model_dump_json()

# WRONG: Not handling validation errors
user = UserCreate(name="", email="invalid", age=-1)  # ValidationError!

# CORRECT: Catch validation errors
from pydantic import ValidationError

try:
    user = UserCreate(name="", email="invalid", age=-1)
except ValidationError as e:
    print(e.errors())  # List of error details
```

## Gotchas
- Pydantic v2 uses `model_dump()` instead of `.dict()`, `model_dump_json()` instead of `.json()`
- `Field(...)` means required; `Field(default=...)` means optional with default
- Use `model_config = ConfigDict(from_attributes=True)` for ORM compatibility
- `field_validator` runs before type coercion; `model_validator` runs after
- Pydantic v2 is 5-50x faster than v1
- Use `Optional[T]` or `T | None` for nullable fields
- `model_dump(exclude_unset=True)` only includes explicitly set fields (useful for PATCH)

## Related
- python/web/fastapi/request-validation.md
- python/stdlib/dataclasses.md
