---
id: "python-stdlib-json-nested"
title: "JSON Parsing: Nested Structures and Custom Encoding"
language: "python"
category: "stdlib"
subcategory: "serialization"
tags: ["json", "parse", "nested", "encoder", "decoder", "serialization"]
version: "3.10+"
retrieval_hint: "JSON parse nested dict list custom encoder decoder datetime serialization"
last_verified: "2026-05-22"
confidence: "high"
---

# JSON Parsing: Nested Structures and Custom Encoding

## When to Use
- Parsing API responses with deeply nested JSON structures
- Serializing Python objects (datetime, dataclass, Enum) to JSON
- Transforming JSON data between different structures (flatten, unflatten)
- Handling JSON with mixed types or missing keys safely

## Standard Pattern

```python
import json
from datetime import datetime, date
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any


# --- Safe nested access ---
def deep_get(data: dict, path: str, default: Any = None) -> Any:
    """Access nested dict keys with dot notation: deep_get(d, 'a.b.c')"""
    keys = path.split(".")
    result = data
    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return default
    return result


# Usage: API response with uncertain structure
response = {"user": {"profile": {"address": {"city": "NYC"}}}}
city = deep_get(response, "user.profile.address.city")  # "NYC"
zip_code = deep_get(response, "user.profile.address.zip", "unknown")  # "unknown"


# --- Flatten nested dict ---
def flatten_dict(data: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Flatten nested dict: {'a': {'b': 1}} -> {'a.b': 1}"""
    items: list[tuple[str, Any]] = []
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


# --- Custom JSON encoder ---
class AppEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, set):
            return list(obj)
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        return super().default(obj)


# Usage
data = {"created": datetime.now(), "status": "active", "tags": {"a", "b"}}
json_str = json.dumps(data, cls=AppEncoder, indent=2)


# --- Custom decoder with object_hook ---
def decode_datetime(obj: dict) -> dict:
    """Convert ISO datetime strings back to datetime objects."""
    for key, value in obj.items():
        if isinstance(value, str):
            try:
                obj[key] = datetime.fromisoformat(value)
            except (ValueError, TypeError):
                pass
    return obj


parsed = json.loads(json_str, object_hook=decode_datetime)


# --- Parse JSONL (JSON Lines) ---
def read_jsonl(path: str) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]
```

## Common Mistakes

```python
# WRONG: KeyError on nested access
city = response["user"]["profile"]["address"]["city"]  # KeyError if any key missing

# CORRECT: Use .get() chain or deep_get
city = response.get("user", {}).get("profile", {}).get("address", {}).get("city")
# Or: deep_get(response, "user.profile.address.city")

# WRONG: Can't serialize datetime to JSON
json.dumps({"created": datetime.now()})  # TypeError: Object of type datetime is not JSON serializable

# CORRECT: Use custom encoder or default parameter
json.dumps({"created": datetime.now()}, default=str)  # Quick: converts to string
# Or: json.dumps(data, cls=AppEncoder)

# WRONG: Parsing JSON with mixed types unsafely
items = json.loads(data)  # Could be dict, list, str, int...
for item in items:  # TypeError if items is a dict
    process(item)

# CORRECT: Validate type before iterating
items = json.loads(data)
if not isinstance(items, list):
    raise ValueError(f"Expected list, got {type(items).__name__}")

# WRONG: json.dumps with non-serializable object silently failing
json.dumps({"set": {1, 2, 3}})  # TypeError

# CORRECT: Handle all types in encoder
class AppEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)
```

## Gotchas
- `json.loads()` returns `str` keys, not `bytes` — use `data.decode()` if reading from binary
- JSON only supports `str`, `int`, `float`, `bool`, `None`, `list`, `dict` — everything else needs a custom encoder
- `object_hook` is called for every JSON object (dict) — use `object_pairs_hook` for ordered access
- `json.dumps(sort_keys=True)` ensures deterministic output (useful for hashing/comparison)
- `float("inf")` and `float("nan")` are not valid JSON — `json.dumps` raises by default, use `allow_nan=True`
- Use `json.loads(..., parse_float=Decimal)` for precise decimal parsing (financial data)
- JSONL (one JSON object per line) is common for log files and streaming APIs
- `default` parameter in `json.dumps` is only called for non-serializable objects

## Related
- python/data/pydantic-v2/computed-validators.md
- python/stdlib/file-io.md
- python/web/fastapi/request-validation.md
