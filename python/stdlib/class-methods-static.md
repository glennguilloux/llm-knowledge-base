---
id: "python-stdlib-class-methods-static"
title: "Class Methods, Static Methods, and Instance Methods"
language: "python"
category: "stdlib"
tags: ["classmethod", "staticmethod", "instance-method", "self", "cls", "OOP"]
version: "3.10+"
retrieval_hint: "classmethod staticmethod instance method self cls OOP class"
last_verified: "2026-05-24"
confidence: "high"
---

# Class Methods, Static Methods, and Instance Methods

## When to Use
- `@classmethod` for alternative constructors (factory methods) or operations on the class itself
- `@staticmethod` for utility functions that logically belong to a class but don't need `self` or `cls`
- Instance methods (default) when you need access to instance state via `self`
- `@classmethod` when you need to access or modify class-level state shared across instances

## Standard Pattern

```python
from __future__ import annotations

import json
from datetime import datetime
from typing import Self


class DateRange:
    """Demonstrates instance, class, and static methods."""

    def __init__(self, start: datetime, end: datetime) -> None:
        if end < start:
            raise ValueError("end must be >= start")
        self.start = start
        self.end = end

    # Instance method — operates on self
    def duration_days(self) -> int:
        """Return the number of days in this range."""
        return (self.end - self.start).days

    def contains(self, date: datetime) -> bool:
        """Check if a date falls within this range."""
        return self.start <= date <= self.end

    # Class method — operates on cls, used as alternative constructor
    @classmethod
    def from_iso_strings(cls, start_str: str, end_str: str) -> Self:
        """Create a DateRange from ISO format strings."""
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)
        return cls(start, end)

    @classmethod
    def from_json(cls, data: str) -> Self:
        """Create a DateRange from a JSON string."""
        parsed = json.loads(data)
        return cls.from_iso_strings(parsed["start"], parsed["end"])

    @classmethod
    def today_only(cls) -> Self:
        """Create a DateRange for today."""
        now = datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59)
        return cls(start, end)

    # Static method — no access to self or cls
    @staticmethod
    def is_valid_range(start: datetime, end: datetime) -> bool:
        """Check if start <= end without creating an instance."""
        return end >= start

    @staticmethod
    def overlap_days(a_start: datetime, a_end: datetime,
                     b_start: datetime, b_end: datetime) -> int:
        """Calculate overlap between two date ranges."""
        latest_start = max(a_start, b_start)
        earliest_end = min(a_end, b_end)
        if latest_start >= earliest_end:
            return 0
        return (earliest_end - latest_start).days

    def __repr__(self) -> str:
        return f"DateRange({self.start!r}, {self.end!r})"


# Usage
if __name__ == "__main__":
    # Instance method
    dr = DateRange.from_iso_strings("2025-01-01", "2025-12-31")
    print(f"Duration: {dr.duration_days()} days")

    # Class method as factory
    today = DateRange.today_only()
    print(f"Today: {today}")

    # Static method — call on class or instance
    print(DateRange.is_valid_range(dr.start, dr.end))  # True
    print(dr.is_valid_range(dr.start, dr.end))  # Also works
```

## Common Mistakes

```python
# WRONG: Using @staticmethod when you need the class for subclassing
class Base:
    @staticmethod
    def create():
        return Base()  # Hardcoded — subclasses get Base, not their type!

class Child(Base):
    pass

obj = Child.create()
print(type(obj))  # <class 'Base'> — not Child!

# CORRECT: Use @classmethod so cls refers to the actual class
class Base:
    @classmethod
    def create(cls):
        return cls()  # Uses the calling class

class Child(Base):
    pass

obj = Child.create()
print(type(obj))  # <class 'Child'>

# WRONG: Forgetting self in an instance method
class Greeter:
    def __init__(self, name: str) -> None:
        self.name = name

    def greet():  # Missing self!
        return f"Hello, {self.name}"

g = Greeter("World")
g.greet()  # TypeError: greet() takes 0 positional arguments but 1 was given

# CORRECT: Always include self as the first parameter
class Greeter:
    def __init__(self, name: str) -> None:
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}"

# WRONG: Using @classmethod but naming the parameter self
class MyClass:
    @classmethod
    def create(self):  # Confusing — should be cls
        return self()

# CORRECT: Use cls for classmethods, self for instance methods
class MyClass:
    @classmethod
    def create(cls):
        return cls()

# WRONG: Putting mutable default logic in @staticmethod that should be class-level
class Counter:
    count = 0

    @staticmethod
    def increment():
        Counter.count += 1  # Hardcoded class name — breaks on subclass

# CORRECT: Use @classmethod to reference the actual class
class Counter:
    count = 0

    @classmethod
    def increment(cls):
        cls.count += 1
```

## Gotchas
- `@classmethod` receives the class as the first argument (`cls`); `@staticmethod` receives neither `self` nor `cls`
- Subclassing a `@classmethod` passes the subclass as `cls`, enabling polymorphic factory methods
- Subclassing a `@staticmethod` gives no such benefit — it always references the class it's defined in
- You CAN call a `@staticmethod` on an instance (`obj.static_method()`), but it's misleading — prefer `Class.static_method()`
- `@classmethod` can access and modify class variables; `@staticmethod` cannot without hardcoding the class name
- Python 3.11+ introduced `Self` in `typing` for return types of classmethods that return an instance
- Overusing `@staticmethod` is a code smell — consider whether the function should be a module-level function instead

## Related
- python/stdlib/dataclasses.md
- python/stdlib/decorators.md
