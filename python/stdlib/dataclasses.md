---
id: "python-stdlib-dataclasses"
title: "Data Classes with @dataclass"
language: "python"
category: "stdlib"
subcategory: "data-structures"
tags: ["dataclass", "data-classes", "immutable", "frozen", "typing"]
version: "3.10+"
retrieval_hint: "dataclass immutable frozen typed data structure"
last_verified: "2026-05-22"
confidence: "high"
---

# Data Classes with @dataclass

## When to Use
- Defining simple data containers with type hints
- Replacing boilerplate `__init__`, `__repr__`, `__eq__` methods
- Creating immutable data structures (with `frozen=True`)
- Building value objects and DTOs

## Standard Pattern

```python
from dataclasses import dataclass, field


@dataclass
class User:
    """Basic mutable dataclass."""
    name: str
    email: str
    age: int
    is_active: bool = True


@dataclass(frozen=True)
class Point:
    """Immutable dataclass (hashable, usable as dict key)."""
    x: float
    y: float


@dataclass
class Config:
    """Dataclass with default factory."""
    name: str
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


# Usage
user = User(name="Alice", email="alice@example.com", age=30)
print(user)  # User(name='Alice', email='alice@example.com', age=30, is_active=True)

point = Point(1.0, 2.0)
# point.x = 3.0  # FrozenInstanceError

config = Config(name="app")
config.tags.append("production")  # Works because list is mutable
```

## Common Mistakes

```python
# WRONG: Using mutable default arguments
@dataclass
class Bad:
    items: list = []  # Shared across all instances!

# CORRECT: Use field(default_factory=...)
@dataclass
class Good:
    items: list = field(default_factory=list)

# WRONG: Forgetting frozen=True when you need immutability
@dataclass
class MutablePoint:
    x: float
    y: float

# Can be accidentally mutated
p = MutablePoint(1.0, 2.0)
p.x = 99.0  # No error, but may break assumptions

# CORRECT: Use frozen=True for immutable data
@dataclass(frozen=True)
class ImmutablePoint:
    x: float
    y: float

# p = ImmutablePoint(1.0, 2.0)
# p.x = 99.0  # FrozenInstanceError

# WRONG: Using dataclass for complex business logic
@dataclass
class Order:
    items: list
    # Complex validation, computed properties, etc. — use a regular class

# CORRECT: Use dataclass for simple data, regular class for complex behavior
```

## Gotchas
- `frozen=True` makes the dataclass hashable (usable as dict key or set member)
- `field(default_factory=list)` creates a new list for each instance
- `__post_init__` runs after `__init__` — use for validation or computed fields
- Use `field(repr=False)` to hide sensitive fields from `__repr__`
- `@dataclass(slots=True)` (Python 3.10+) reduces memory usage
- `dataclasses.asdict()` creates a deep copy — nested mutable objects are copied
- Use `@dataclass(order=True)` to enable `<`, `>`, `<=`, `>=` comparisons

## Related
- python/data/pydantic-v2/models.md
- python/stdlib/typing-advanced.md
