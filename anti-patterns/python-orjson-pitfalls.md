---
id: "anti-patterns-python-orjson-pitfalls"
title: "Python Anti-Pattern: orjson Pitfalls vs stdlib json"
language: "python"
category: "anti-patterns"
tags: ["antipatterns", "python", "json", "orjson", "serialization", "performance"]
version: "n/a"
retrieval_hint: "orjson vs json performance bytes vs str datetime UUID Decimal OPT_INDENT_2 options sort_keys pretty print"
last_verified: "2026-05-24"
confidence: "high"
---

# Python Anti-Pattern: orjson Pitfalls vs stdlib json

## When to Use
- Working with performance-critical JSON serialization in Python
- Handling non-standard JSON types (datetime, UUID, bytes, numpy)
- Replacing stdlib `json` with `orjson` for 4-10x speedup
- Reviewing code that mixes `json` and `orjson` APIs incorrectly

## Standard Pattern

```python
import json
import orjson
from datetime import datetime, date, timezone

# WRONG: Assuming orjson.dumps returns str like json.dumps
data = {"key": "value"}
result = orjson.dumps(data)
print(result)               # b'{"key":"value"}' — bytes, not str!
formatted = result.strip()  # TypeError: expected str, got bytes

# CORRECT: Decode bytes to str explicitly
result = orjson.dumps(data).decode("utf-8")
print(result)               # {"key":"value"}

# WRONG: Expecting pretty-print via indent param (json compat)
data = {"z": 1, "a": 2}
print(json.dumps(data, indent=2))
# {
#   "z": 1,
#   "a": 2
# }
print(orjson.dumps(data))   # b'{"a":1,"z":1}' — no indent, keys sorted

# CORRECT: Use OPT_INDENT_2 for pretty output
print(orjson.dumps(data, option=orjson.OPT_INDENT_2).decode())
# {
#   "a": 1,
#   "z": 1
# }

# WRONG: Trying to disable key sorting (json.dumps has sort_keys=False by default)
data = {"z": 1, "a": 2}
json.dumps(data)                    # '{"z": 1, "a": 2}' — insertion order
orjson.dumps(data)                  # b'{"a":1,"z":1}' — always sorted!

# CORRECT: orjson ALWAYS sorts keys — no opt-out
# If insertion order is required, use json.dumps() instead
# Note: orjson OPT_SORT_KEYS is the default; you cannot disable it
data = {"z": 1, "a": 2}
# Will always be sorted alphabetically
sorted_str = orjson.dumps(data).decode()  # '{"a":1,"z":1}'

# WRONG: Handling datetime without custom serializer (json compat mode)
from datetime import datetime
obj = {"timestamp": datetime(2024, 1, 15, 12, 30, 0, tzinfo=timezone.utc)}
json.dumps(obj)                     # TypeError: Object of type datetime is not JSON serializable

# CORRECT: orjson handles datetime natively
result = orjson.dumps(obj).decode()
print(result)   # {"timestamp":"2024-01-15T12:30:00+00:00"}

# WRONG: orjson default= handler vs json default= handler (different calling convention)
def json_fallback(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError

# json.dumps passes the object to default= directly
json.dumps({"val": Decimal("10.5")}, default=json_fallback)  # works

# orjson.dumps passes the object to default= directly
orjson.dumps({"val": Decimal("10.5")}, default=json_fallback)  # same pattern

# WRONG: Using orjson.loads on malformed JSON (less informative errors)
try:
    orjson.loads(b"{invalid}")
except orjson.JSONDecodeError as e:
    print(f"Parse error at column {e.col()}")  # More informative than json

# WRONG: Assuming ensure_ascii=False behavior
data = {"msg": "héllo"}
json.dumps(data)                   # '{"msg": "h\\u00e9llo"}' — escaped
json.dumps(data, ensure_ascii=False)  # '{"msg": "héllo"}' — raw

orjson.dumps(data).decode()        # '{"msg":"héllo"}' — ALWAYS raw UTF-8
# orjson has no ensure_ascii option — it always outputs UTF-8

# WRONG: Passing json.dumps kwargs to orjson (most are unsupported)
data = {"key": "value"}
try:
    orjson.dumps(data, cls=MyEncoder)   # TypeError: unexpected keyword argument
except TypeError:
    pass  # orjson doesn't support custom encoder classes

# WRONG: Serializing numpy floats (int64 overflow)
import numpy as np
# orjson DOES handle numpy types natively (unlike json)
data = {"val": np.float64(3.14)}
result = orjson.dumps(data).decode()
print(result)   # {"val":3.14} — works out of the box
```

## Common Mistakes
The most common pitfall is forgetting that `orjson.dumps()` returns `bytes`, not `str`. Every call needs `.decode("utf-8")`. Second: orjson ALWAYS sorts dictionary keys alphabetically with no opt-out — if you need insertion order, use stdlib `json`. Third: orjson has no `indent`, `sort_keys`, `ensure_ascii`, or `cls` parameters — it uses `option` flags instead. Fourth: orjson handles `datetime`, `date`, `UUID`, `bytes`, and numpy types natively, so if you were using custom `default=` handlers for these, they'll conflict.

## Gotchas
- `orjson.dumps()` returns `bytes` — always call `.decode("utf-8")` for string output; forgetting this causes cryptic `TypeError` downstream
- Keys are ALWAYS sorted alphabetically; there is no `sort_keys=False` — use stdlib `json` if you need insertion order
- No `indent` parameter — use `orjson.OPT_INDENT_2` for 2-space indentation
- No `ensure_ascii` parameter — orjson always outputs raw UTF-8 (no `\uXXXX` escapes)
- No `default=` for datetime, UUID, date, bytes, numpy types — they're built in; your custom `default=` will NOT be called for these
- `orjson.loads()` requires `bytes` input, not `str` — unlike `json.loads()` which accepts both
- `orjson.OPT_SERIALIZE_NUMPY` enables numpy array serialization (not enabled by default for numpy)
- `orjson.OPT_OMIT_MICROSECONDS` strips microseconds from datetime serialization
- `orjson.OPT_NAIVE_UTC` treats naive datetime objects as UTC (otherwise they raise)
- `orjson.OPT_NON_STR_KEYS` serializes non-string dict keys (json would raise TypeError)
- Decimal types are NOT natively supported — you need a `default=` handler for these
- orjson raises `orjson.JSONDecodeError` (subclass of `ValueError`) on parse failures, which is more detailed than `json.JSONDecodeError`
- Mixing `orjson` and `json` in the same project often leads to confusion about return types — standardize on one per module

## Related
- anti-patterns/python-antipatterns.md
- python/stdlib/json-nested.md
