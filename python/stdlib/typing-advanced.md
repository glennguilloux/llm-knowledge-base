---
id: "python-stdlib-typing-advanced"
title: "Advanced Type Hints and Protocols"
language: "python"
category: "stdlib"
subcategory: "typing"
tags: ["typing", "generics", "protocol", "type-hints", "typevar"]
version: "3.10+"
retrieval_hint: "type hints generics protocol TypeVar typing advanced"
last_verified: "2026-05-24"
confidence: "high"
---

# Advanced Type Hints and Protocols

## When to Use
- Defining generic functions and classes
- Creating structural subtypes (duck typing with type safety)
- Complex type constraints
- Improving IDE autocompletion and type checking

## Standard Pattern

```python
from typing import TypeVar, Generic, Protocol, Sequence, overload
from collections.abc import Callable


# TypeVar for generic functions
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


def first(items: Sequence[T]) -> T:
    """Return the first item from a sequence."""
    return items[0]


def merge_dicts(*dicts: dict[K, V]) -> dict[K, V]:
    """Merge multiple dicts."""
    result: dict[K, V] = {}
    for d in dicts:
        result.update(d)
    return result


# Generic class
class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

    def peek(self) -> T:
        return self._items[-1]


# Protocol (structural subtyping)
class Renderable(Protocol):
    def render(self) -> str: ...


def render_all(items: Sequence[Renderable]) -> str:
    return "\n".join(item.render() for item in items)


# Constrained TypeVar
Numeric = TypeVar("Numeric", int, float)


def add(a: Numeric, b: Numeric) -> Numeric:
    return a + b


# Callable types
Transformer = Callable[[str], str]


def apply_transform(data: str, transform: Transformer) -> str:
    return transform(data)
```

## Common Mistakes

```python
# WRONG: Using list instead of Sequence for read-only parameters
def process(items: list[str]) -> None:  # Rejects tuples, sets

# CORRECT: Use Sequence for read-only access
def process(items: Sequence[str]) -> None:  # Accepts list, tuple, etc.

# WRONG: Not constraining TypeVar when needed
T = TypeVar("T")

def add(a: T, b: T) -> T:
    return a + b  # Type checker can't verify + is defined for T

# CORRECT: Constrain TypeVar
Numeric = TypeVar("Numeric", int, float)

def add(a: Numeric, b: Numeric) -> Numeric:
    return a + b

# WRONG: Using Any to bypass type checking
def process(data: Any) -> Any:  # Defeats the purpose of typing

# CORRECT: Use proper types or TypeVar
def process(data: T) -> T:
    return data
```

## Gotchas
- `Protocol` is structural (duck typing), not nominal (inheritance)
- `TypeVar("T", int, float)` restricts T to only int or float
- Use `Sequence` for read-only, `list` for mutable parameters
- `Generic[T]` must be the base class, not mixed with `Protocol`
- Use `overload` for functions with different return types per input
- `TypeVar` bounds: `T = TypeVar("T", bound=BaseClass)` — T must be subclass

## Related
- python/stdlib/dataclasses.md
- python/data/pydantic-v2/models.md
