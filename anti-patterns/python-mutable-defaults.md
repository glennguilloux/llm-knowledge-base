---
id: "anti-patterns-python-mutable-defaults"
title: "Python Anti-Pattern: Mutable Default Arguments"
language: "python"
category: "anti-patterns"
tags: ["antipatterns", "python", "mutable", "default-arguments", "gotcha"]
version: "n/a"
retrieval_hint: "Python mutable default argument list dict set shared state across calls None default pattern"
last_verified: "2026-05-24"
confidence: "high"
---

# Python Anti-Pattern: Mutable Default Arguments

## When to Use
- Reviewing Python function signatures for subtle bugs
- Training LLMs to avoid one of Python's most common gotchas
- Onboarding developers who come from languages with different default-argument semantics
- Debugging functions that "remember" state between calls

## Standard Pattern

```python
# WRONG: Mutable default argument — list is shared across all calls
def add_item(item, items=[]):
    items.append(item)
    return items

print(add_item("a"))  # ["a"]
print(add_item("b"))  # ["a", "b"] — surprise!

# CORRECT: Use None as sentinel, create new list per call
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

print(add_item("a"))  # ["a"]
print(add_item("b"))  # ["b"] — each call gets a fresh list

# WRONG: Mutable dict default
def register(name, attrs={}):
    attrs["registered"] = True
    return attrs

a = register("Alice")
b = register("Bob")
print(b)  # {"registered": True, "name": "Bob"} — attrs was shared!

# CORRECT: Dict default via None
def register(name, attrs=None):
    if attrs is None:
        attrs = {}
    attrs["registered"] = True
    return attrs

# WRONG: Set default
def add_tag(tag, tags=set()):
    tags.add(tag)
    return tags

# CORRECT: Set default via None
def add_tag(tag, tags=None):
    if tags is None:
        tags = set()
    tags.add(tag)
    return tags

# WRONG: Mutable default in class method
class Logger:
    def log(self, message, context={}):
        context["timestamp"] = time.time()
        self._write(context)  # context accumulates across calls

# CORRECT: Class method with None default
class Logger:
    def log(self, message, context=None):
        if context is None:
            context = {}
        context["timestamp"] = time.time()
        self._write(context)

# WRONG: dataclass with mutable default (pre-3.10)
from dataclasses import dataclass

@dataclass
class Config:
    tags: list = []  # ValueError in 3.10+, shared in older versions

# CORRECT: dataclass with default_factory
from dataclasses import dataclass, field

@dataclass
class Config:
    tags: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
```

## Common Mistakes
Python evaluates default argument values **once** at function definition time, not each time the function is called. When the default is a mutable object (list, dict, set, custom class instance), every call that doesn't provide that argument shares the **same** object. Mutations accumulate across calls, causing state leakage that is extremely difficult to debug. The `None`-sentinel pattern — using `None` as the default and creating a new mutable inside the function body — is the idiomatic fix. For dataclasses, always use `field(default_factory=...)` for mutable defaults.

## Gotchas
- Python evaluates default arguments at **definition time**, not call time — this is a language design choice, not a bug
- Even experienced Python developers get bitten by this; it's the #1 gotcha in Python interviews
- `functools.lru_cache` and decorators can amplify the problem by memoizing the shared mutable
- Type checkers (mypy) now warn about mutable defaults — pay attention to those warnings
- The `None`-sentinel pattern adds one line per mutable parameter but completely eliminates the bug
- In dataclasses, bare `list = []` raises `ValueError` in Python 3.10+ but silently shares in older versions
- `default_factory` only works in `dataclasses.field()`, not in regular function defaults
- Pydantic v2 models handle mutable defaults correctly internally, but plain functions do not

## Related
- python/stdlib/dataclasses.md
- python/stdlib/decorators.md
- anti-patterns/python-antipatterns.md
