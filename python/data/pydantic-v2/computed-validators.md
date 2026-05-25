---
id: "python-data-pydantic-v2-computed-validators"
title: "Pydantic v2 Computed Fields, Validators, and JSON Schema"
language: "python"
category: "data"
subcategory: "validation"
tags: ["pydantic", "validation", "computed", "json-schema", "settings", "model"]
version: "3.10+"
retrieval_hint: "Pydantic v2 computed field validator JSON schema settings env"
last_verified: "2026-05-24"
confidence: "high"
---

# Pydantic v2 Computed Fields, Validators, and JSON Schema

## When to Use
- Deriving fields from other fields (full_name from first + last)
- Custom validation logic beyond simple type checking (email domain, date ranges)
- Generating JSON Schema for API documentation or form generation
- Loading configuration from environment variables with validation

## Standard Pattern

```python
from pydantic import BaseModel, Field, field_validator, model_validator, computed_field
from pydantic_settings import BaseSettings
from datetime import date, datetime
from typing import Annotated


# --- Computed fields ---
class User(BaseModel):
    first_name: str
    last_name: str
    birth_date: date

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @computed_field
    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )


user = User(first_name="Alice", last_name="Smith", birth_date=date(1990, 5, 15))
print(user.full_name)  # "Alice Smith"
print(user.model_dump())  # includes full_name and age


# --- Field validators ---
class Order(BaseModel):
    email: Annotated[str, Field(min_length=5)]
    quantity: Annotated[int, Field(gt=0, le=1000)]
    coupon_code: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, v: str) -> str:
        allowed_domains = {"example.com", "company.org"}
        domain = v.split("@")[-1].lower()
        if domain not in allowed_domains:
            raise ValueError(f"Email domain must be one of {allowed_domains}")
        return v.lower()

    @field_validator("coupon_code")
    @classmethod
    def normalize_coupon(cls, v: str | None) -> str | None:
        if v is not None:
            return v.upper().strip()
        return v


# --- Model validator (cross-field) ---
class DateRange(BaseModel):
    start: date
    end: date

    @model_validator(mode="after")
    def validate_range(self) -> "DateRange":
        if self.end < self.start:
            raise ValueError("end must be after start")
        return self


# --- JSON Schema generation ---
schema = User.model_json_schema()
# Returns dict with properties, required, types — use for form generation, docs


# --- Settings from environment ---
class AppSettings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    debug: bool = False
    log_level: str = "INFO"
    api_key: str = Field(..., min_length=10)

    model_config = {"env_file": ".env", "env_prefix": "APP_"}


# Usage: APP_DATABASE_URL, APP_REDIS_URL, APP_DEBUG, etc. from env
settings = AppSettings()
```

## Common Mistakes

```python
# WRONG: Using v1-style @validator
from pydantic import validator  # Deprecated in v2

class User(BaseModel):
    name: str

    @validator("name")  # v1 API
    def check_name(cls, v):
        return v.strip()

# CORRECT: Use @field_validator in v2
from pydantic import field_validator

class User(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str) -> str:
        return v.strip()

# WRONG: Mutating input in validator
@field_validator("tags")
@classmethod
def validate_tags(cls, v: list[str]) -> list[str]:
    v.clear()  # Mutates the original list!
    return v

# CORRECT: Return a new value
@field_validator("tags")
@classmethod
def validate_tags(cls, v: list[str]) -> list[str]:
    return [t.strip().lower() for t in v]

# WRONG: Forgetting @classmethod on field_validator
@field_validator("email")
def validate_email(cls, v):  # Missing @classmethod!

# CORRECT: Always add @classmethod
@field_validator("email")
@classmethod
def validate_email(cls, v: str) -> str:
    return v.lower()
```

## Gotchas
- `@field_validator` must have `@classmethod` decorator — Pydantic v2 requires it
- `mode="after"` validators receive the model instance, not the raw value
- `@computed_field` values appear in `model_dump()` and `model_json_schema()` automatically
- `pydantic-settings` is a separate package (`pip install pydantic-settings`)
- `model_json_schema()` produces JSON Schema draft 2020-12 — compatible with OpenAPI 3.1
- Use `Annotated[str, Field(...)]` instead of `str = Field(...)` for clearer type hints
- `model_validator(mode="wrap")` gives access to both raw input and the validated model
- Pydantic v2 uses Rust under the hood — significantly faster than v1

## Related
- python/web/fastapi/request-validation.md
- python/data/pydantic-v2/models.md
- python/web/fastapi/basics.md
