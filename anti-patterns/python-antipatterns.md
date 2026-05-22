---
id: "antipatterns-python"
title: "Python Anti-Patterns"
language: "python"
category: "anti-patterns"
tags: ["antipatterns", "python", "common-mistakes", "best-practices"]
version: "n/a"
retrieval_hint: "python common mistakes antipatterns mutable default bare except"
last_verified: "2026-05-22"
confidence: "high"
---

# Python Anti-Patterns

## When to Use
- Reviewing Python code for common mistakes
- Training small LLMs to avoid frequent Python errors
- Code review checklists
- Onboarding developers new to Python

## Standard Pattern

```python
# WRONG: Mutable default argument
def add_item(item, items=[]):
    items.append(item)
    return items

# CORRECT: Use None as sentinel
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

# WRONG: Bare except clause
try:
    result = int(user_input)
except:
    result = 0

# CORRECT: Catch specific exceptions
try:
    result = int(user_input)
except ValueError:
    result = 0

# WRONG: Using == for None comparison
if value == None:
    print("missing")

# CORRECT: Use is for None
if value is None:
    print("missing")

# WRONG: Wildcard import
from os import *

# CORRECT: Explicit imports
from os import path, getcwd, environ

# WRONG: Global variables for state
counter = 0
def increment():
    global counter
    counter += 1

# CORRECT: Use a class or closure
class Counter:
    def __init__(self):
        self.value = 0
    def increment(self):
        self.value += 1

# WRONG: String concatenation in loop
result = ""
for i in range(10000):
    result += str(i)  # O(n^2) — creates new string each time

# CORRECT: Use join or list append
parts = []
for i in range(10000):
    parts.append(str(i))
result = "".join(parts)

# WRONG: Not using enumerate
index = 0
for item in items:
    print(f"{index}: {item}")
    index += 1

# CORRECT: Use enumerate
for index, item in enumerate(items):
    print(f"{index}: {item}")

# WRONG: Catching broad Exception silently
try:
    process_data()
except Exception:
    pass  # Swallows all errors

# CORRECT: Log or re-raise
try:
    process_data()
except Exception:
    logger.exception("Failed to process data")
    raise

# WRONG: Premature optimization with list comprehension for side effects
[print(x) for x in items]  # Creates useless list of Nones

# CORRECT: Use a for loop for side effects
for x in items:
    print(x)

# WRONG: Checking type with ==
if type(value) == str:
    process_string(value)

# CORRECT: Use isinstance
if isinstance(value, str):
    process_string(value)
```

## Common Mistakes
The most damaging Python anti-patterns are mutable default arguments (causes shared state across calls), bare except clauses (hides bugs), and == for None (breaks with custom __eq__). String concatenation in loops causes O(n^2) performance. Wildcard imports pollute the namespace and make dependencies unclear.

## Gotchas
- `is` checks identity, `==` checks equality — always use `is` for None, True, False
- Mutable defaults are evaluated once at function definition, not each call
- `except Exception` still catches system exits — use `except (ValueError, TypeError)` for specific errors
- List comprehensions are for creating lists, not side effects
- `type()` does not respect inheritance — always use `isinstance()`
- Global variables make testing difficult and introduce hidden coupling
- `+=` on strings in a loop is O(n^2) due to string immutability

## Related
- python/stdlib/decorators.md
- python/stdlib/file-io.md
- error-handling/structured-errors.md
