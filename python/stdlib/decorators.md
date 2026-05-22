---
id: "python-stdlib-decorators"
title: "Decorators and Closure Patterns"
language: "python"
category: "stdlib"
tags: ["decorators", "closures", "functools", "wraps", "higher-order"]
version: "3.10+"
retrieval_hint: "decorator closure functools wraps higher-order function"
last_verified: "2026-05-22"
confidence: "high"
---

# Decorators and Closure Patterns

## When to Use
- Cross-cutting concerns (logging, timing, auth)
- Modifying function behavior without changing the function
- Creating reusable function wrappers
- Implementing retry logic, caching, rate limiting

## Standard Pattern

```python
import functools
import time
import logging

logger = logging.getLogger(__name__)

# Basic decorator
def log_calls(func):
    @functools.wraps(func)  # Preserves __name__, __doc__, etc.
    def wrapper(*args, **kwargs):
        logger.info("Calling %s with args=%s kwargs=%s", func.__name__, args, kwargs)
        result = func(*args, **kwargs)
        logger.info("%s returned %s", func.__name__, result)
        return result
    return wrapper

@log_calls
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

# Decorator with arguments
def retry(max_attempts: int = 3, delay: float = 1.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        raise
                    logger.warning("Attempt %d failed: %s", attempt, e)
                    time.sleep(delay * attempt)
        return wrapper
    return decorator

@retry(max_attempts=3, delay=0.5)
def fetch_data(url: str) -> dict:
    """Fetch data from URL with retry."""
    import httpx
    return httpx.get(url).json()

# Timing decorator
def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info("%s took %.3f seconds", func.__name__, elapsed)
        return result
    return wrapper

# Class-based decorator
class Cache:
    def __init__(self, maxsize: int = 128):
        self.maxsize = maxsize
        self.cache = {}

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args):
            if args in self.cache:
                return self.cache[args]
            result = func(*args)
            if len(self.cache) >= self.maxsize:
                self.cache.pop(next(iter(self.cache)))
            self.cache[args] = result
            return result
        return wrapper

@Cache(maxsize=256)
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# Property decorator
class User:
    def __init__(self, first_name: str, last_name: str):
        self._first_name = first_name
        self._last_name = last_name

    @property
    def full_name(self) -> str:
        return f"{self._first_name} {self._last_name}"

    @full_name.setter
    def full_name(self, value: str) -> None:
        parts = value.split(" ", 1)
        self._first_name = parts[0]
        self._last_name = parts[1] if len(parts) > 1 else ""

# Stacking decorators
@log_calls
@timer
@retry(max_attempts=2)
def important_operation(data: dict) -> dict:
    """Process with logging, timing, and retry."""
    return process(data)
```

## Common Mistakes

```python
# WRONG: Missing functools.wraps
def my_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def example():
    """Docstring."""
    pass

print(example.__name__)  # "wrapper" — lost original name!

# CORRECT: Use functools.wraps
def my_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def example():
    """Docstring."""
    pass

print(example.__name__)  # "example" — preserved!

# WRONG: Decorator without arguments that looks like it takes them
@my_decorator  # This works
def func(): pass

@my_decorator()  # This fails — my_decorator doesn't return a decorator
def func(): pass

# CORRECT: Make decorator work both ways
def my_decorator(func=None):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    if func is not None:
        return decorator(func)
    return decorator

# WRONG: Not handling method decorators properly
def validate(func):
    def wrapper(*args):  # Breaks for methods — missing self
        return func(*args)
    return wrapper

# CORRECT: Accept *args, **kwargs
def validate(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
```

## Gotchas
- `functools.wraps` preserves `__name__`, `__doc__`, `__module__`, and `__wrapped__` — always use it
- Decorators with arguments require an extra layer of nesting (decorator factory pattern)
- Stacking order matters — `@A @B @C def f()` runs as `A(B(C(f)))`, so A is outermost
- `@property` creates a descriptor — it only works on class attributes, not instance attributes
- Decorators run at import time, not call time — the wrapper is created when the module loads
- `functools.lru_cache` is a built-in memoization decorator — prefer it over rolling your own
- `functools.singledispatch` enables function overloading by type
- Decorators can be applied to classes too (`@dataclass`, `@functools.total_ordering`)

## Related
- python/stdlib/context-managers.md
- python/stdlib/typing-advanced.md
- python/patterns/retry-logic.md
