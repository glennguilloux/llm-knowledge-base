---
id: "python-stdlib-str-vs-repr"
title: "__str__ vs __repr__ for Object Representation"
language: "python"
category: "stdlib"
tags: ["str", "repr", "dunder", "string-representation", "format", "__format__"]
version: "3.10+"
retrieval_hint: "__str__ __repr__ string representation format dunder"
last_verified: "2026-05-24"
confidence: "high"
---

# __str__ vs __repr__ for Object Representation

## When to Use
- Every class should define `__repr__` for unambiguous developer-facing output
- Define `__str__` for user-friendly display output
- `print()` uses `__str__`, falling back to `__repr__`
- Interactive interpreter / debugger uses `__repr__`
- `format()` and f-strings use `__format__`, falling back to `__str__`

## Standard Pattern

```python
from datetime import datetime


class Point:
    """Example: proper __repr__ and __str__ implementation."""

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        """Unambiguous — should ideally allow eval(repr(obj)) == obj."""
        return f"Point(x={self.x!r}, y={self.y!r})"

    def __str__(self) -> str:
        """Human-readable — for end users."""
        return f"({self.x}, {self.y})"


p = Point(3.0, 4.0)
print(repr(p))   # Point(x=3.0, y=4.0)
print(str(p))    # (3.0, 4.0)
print(p)         # (3.0, 4.0) — uses __str__
print(f"{p}")    # (3.0, 4.0) — uses __str__
print(f"{p!r}")  # Point(x=3.0, y=4.0) — uses __repr__


# --- Best practice: always define __repr__, __str__ is optional ---

class Task:
    """If you only define one, make it __repr__."""

    def __init__(self, name: str, priority: int, done: bool = False) -> None:
        self.name = name
        self.priority = priority
        self.done = done

    def __repr__(self) -> str:
        return (
            f"Task(name={self.name!r}, priority={self.priority!r}, "
            f"done={self.done!r})"
        )

t = Task("deploy", 1)
print(t)  # Task(name='deploy', priority=1, done=False)
# __str__ falls back to __repr__


# --- __format__ for custom formatting ---

class Money:
    def __init__(self, amount: float, currency: str = "USD") -> None:
        self.amount = amount
        self.currency = currency

    def __repr__(self) -> str:
        return f"Money(amount={self.amount!r}, currency={self.currency!r})"

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:,.2f}"

    def __format__(self, format_spec: str) -> str:
        if format_spec == "short":
            return f"{self.currency} {self.amount:.0f}"
        elif format_spec == "accounting":
            return f"{self.currency} {self.amount:,.2f}"
        return str(self)

m = Money(1234.567)
print(f"{m}")           # USD 1,234.57
print(f"{m:short}")     # USD 1235
print(f"{m:accounting}") # USD 1,234.57


# --- Using dataclass (auto-generates __repr__ and __init__) ---

from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str
    active: bool = True

u = User("Alice", "alice@example.com")
print(repr(u))  # User(name='Alice', email='alice@example.com', active=True)
print(u)        # User(name='Alice', email='alice@example.com', active=True)
```

## Common Mistakes

```python
# WRONG: __repr__ returns something that looks like __str__
class Bad:
    def __repr__(self):
        return "Bad instance"  # Not unambiguous!

# CORRECT: __repr__ should include class name and key state
class Good:
    def __repr__(self):
        return f"Good()"
# Ideally: eval(repr(obj)) works, but if not possible, at least show all state

# WRONG: Using %s in f-string representation
class Bad:
    def __repr__(self):
        return f"Bad(x={self.x})"  # No !r — ambiguous types

b = Bad(x="hello")
# Bad(x=hello) — is that a variable or a string?

# CORRECT: Use !r for repr of individual values
class Good:
    def __repr__(self):
        return f"Good(x={self.x!r})"
# Good(x='hello') — clearly a string

# WRONG: Side effects in __repr__ or __str__
class Bad:
    def __repr__(self):
        self.counter = getattr(self, "counter", 0) + 1
        return f"Bad(counter={self.counter})"  # Side effect!

# CORRECT: String methods should be pure (no side effects)
class Good:
    def __repr__(self):
        return f"Good(x={self.x!r})"

# WRONG: __repr__ returns None (forgot return)
class Bad:
    def __repr__(self):
        print(f"Bad(x={self.x})")  # Prints but returns None!

b = Bad(x=42)
print(b)  # TypeError: __repr__ returned non-string (type NoneType)

# CORRECT: Always return a string
class Good:
    def __repr__(self) -> str:
        return f"Good(x={self.x!r})"
```

## Gotchas
- If only `__repr__` is defined, `str()` falls back to it — so always define `__repr__`
- `!r` in f-strings calls `repr()` on the value — `f"{obj!r}"` vs `f"{obj}"` uses `str()`
- `__repr__` should ideally return a string that could recreate the object with `eval()` — but this is a guideline, not a strict rule
- `collections.namedtuple` auto-generates a good `__repr__` — pattern: `Point(x=1, y=2)`
- `dataclasses.dataclass` auto-generates `__repr__` and `__eq__` — use it!
- `__str__` and `__repr__` must return `str` — returning anything else raises `TypeError`
- `__format__` is called by f-strings and `format()` — the `format_spec` string comes after the colon (`f"{obj:spec}"`)
- Logging calls `str()` on arguments; the interactive REPL calls `repr()`
- Container `__str__` uses `repr()` of elements — `str([obj])` calls `repr()` on each element inside the list

## Related
- python/stdlib/class-methods-static.md
- python/stdlib/dataclasses.md
- python/stdlib/decorators.md
