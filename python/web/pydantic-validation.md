---
id: "python-web-pydantic-validation"
title: "Pydantic Validation for Python Web Requests"
language: "python"
category: "web"
subcategory: "validation"
tags: ["pydantic", "validation", "fastapi", "request-body", "query-params", "patch", "errors"]
version: "3.10+"
retrieval_hint: "Pydantic validation FastAPI request body query params PATCH exclude_unset field_validator model_validator ValidationError"
last_verified: "2026-05-24"
confidence: "medium"
---

# Pydantic Validation for Python Web Requests

## When to Use
- Validating JSON request bodies, query parameters, and path parameters in web APIs
- Enforcing business rules that span multiple fields before persistence
- Returning consistent `422 Unprocessable Entity` errors for invalid input
- Supporting partial updates with PATCH semantics
- Serializing response models without leaking internal fields

## Standard Pattern

```python
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

app = FastAPI()

Currency = Literal["USD", "EUR", "GBP"]


class LineItem(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    quantity: int = Field(ge=1, le=1000)
    unit_price: Decimal = Field(gt=Decimal("0"))


class CreateInvoice(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: int = Field(gt=0)
    currency: Currency = "USD"
    line_items: list[LineItem] = Field(min_length=1, max_length=100)
    due_date: date
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("notes")
    @classmethod
    def trim_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def invoice_total_must_be_positive(self) -> "CreateInvoice":
        total = sum(item.quantity * item.unit_price for item in self.line_items)
        if total <= Decimal("0"):
            raise ValueError("invoice total must be positive")
        return self

    @property
    def total(self) -> Decimal:
        return sum(item.quantity * item.unit_price for item in self.line_items).quantize(Decimal("0.01"))


class UpdateInvoice(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    currency: Currency | None = None
    line_items: list[LineItem] | None = None
    due_date: date | None = None
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("notes")
    @classmethod
    def trim_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.get("/health")
async def health(min_version: Annotated[int, Query(ge=1, le=3)] = 1) -> dict:
    return {"ok": True, "min_version": min_version}


@app.post("/invoices")
async def create_invoice(payload: CreateInvoice, dry_run: bool = Query(False)) -> dict:
    if dry_run:
        return {"accepted": False, "total": str(payload.total), "items": len(payload.line_items)}

    saved_id = 123  # Persist before returning in production.
    return {"accepted": True, "invoice_id": saved_id, "total": str(payload.total)}


@app.patch("/invoices/{invoice_id}")
async def patch_invoice(invoice_id: int, payload: UpdateInvoice) -> dict:
    if invoice_id <= 0:
        raise HTTPException(status_code=404, detail="Invoice not found")

    update_data = payload.model_dump(exclude_unset=True, mode="json")
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields supplied")

    return {"invoice_id": invoice_id, "updated_fields": sorted(update_data)}
```

## Common Mistakes

```python
# WRONG: Accepting an untyped dict leaves validation to manual checks
@app.post("/invoices")
async def create_invoice(payload: dict):
    if payload["customer_id"] <= 0:
        raise ValueError("bad customer")

# CORRECT: Use a Pydantic model so FastAPI validates and documents the schema
@app.post("/invoices")
async def create_invoice(payload: CreateInvoice):
    return {"total": str(payload.total)}
```

```python
# WRONG: Mutable defaults are shared across requests
class SearchQuery(BaseModel):
    filters: list[str] = []

# CORRECT: Use Field(default_factory=list) for per-request mutable values
class SearchQuery(BaseModel):
    filters: list[str] = Field(default_factory=list)
```

```python
# WRONG: Using Pydantic v1 serialization in v2
payload.model_dump()       # Correct in v2
payload.model_dump_json()  # Correct in v2

# CORRECT: Keep v1-only APIs out of new code
payload.dict()   # Deprecated
payload.json()   # Deprecated
```

```python
# WRONG: PATCH replaces unset fields with None
update_data = payload.model_dump()  # Includes None for fields not sent

# CORRECT: Exclude unset fields so omitted fields stay unchanged
update_data = payload.model_dump(exclude_unset=True, mode="json")
```

```python
# WRONG: Letting validation errors leak as raw framework details
try:
    CreateInvoice.model_validate(data)
except ValidationError as exc:
    raise HTTPException(status_code=500, detail=str(exc))

# CORRECT: Map validation errors to a controlled 422 response
try:
    CreateInvoice.model_validate(data)
except ValidationError as exc:
    raise RequestValidationError(exc.errors())
```

## Gotchas
- `Field(...)` means required; `Field(default=None)` means optional and present as `None`
- `model_dump(exclude_unset=True)` is the usual choice for PATCH because it preserves omitted fields
- Pydantic v2 uses `model_dump()` and `model_dump_json()` instead of `.dict()` and `.json()`
- `field_validator` defaults to `mode="after"` type coercion; use `mode="before"` explicitly when raw input must be normalized first
- `model_validator(mode="after")` is useful for cross-field rules after individual fields are validated
- `mode="json"` serializes dates, decimals, enums, and other non-JSON-native values for API responses
- `ConfigDict(strict=True)` prevents silent coercion such as `"5"` becoming `5`
- FastAPI already provides a default `422` handler; override it only when a custom error shape is required

## Related
- python/web/fastapi/request-validation.md
- python/web/fastapi/error-handling.md
- python/web/file-uploads.md
