---
id: "python-stdlib-context-managers"
title: "Context Managers with the with Statement"
language: "python"
category: "stdlib"
subcategory: "resource-management"
tags: ["context-manager", "with", "resource", "cleanup", "exception"]
version: "3.10+"
retrieval_hint: "context manager with statement resource cleanup exception"
last_verified: "2026-05-24"
confidence: "high"
---

# Context Managers with the with Statement

## When to Use
- Managing resources that need cleanup (files, connections, locks)
- Ensuring cleanup happens even if exceptions occur
- Setting up and tearing down state (database transactions, test fixtures)
- Acquiring and releasing locks

## Standard Pattern

```python
from contextlib import contextmanager
from typing import Generator


# Built-in context managers
with open("file.txt", "r") as f:
    content = f.read()
# File is automatically closed

with open("output.txt", "w") as f:
    f.write("data")
# File is automatically closed and flushed


# Creating a context manager with @contextmanager
@contextmanager
def timer(label: str) -> Generator[None, None, None]:
    """Context manager that times a block of code."""
    import time
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"{label}: {elapsed:.3f}s")


with timer("my_operation"):
    # Do something
    pass


# Context manager with return value
@contextmanager
def database_connection(url: str):
    """Context manager for database connections."""
    conn = create_connection(url)
    try:
        yield conn
    finally:
        conn.close()


with database_connection("postgresql://...") as conn:
    conn.execute("SELECT 1")


# Class-based context manager
class FileManager:
    def __init__(self, path: str, mode: str = "r"):
        self.path = path
        self.mode = mode
        self.file = None

    def __enter__(self):
        self.file = open(self.path, self.mode)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
        return False  # Don't suppress exceptions


with FileManager("data.txt", "w") as f:
    f.write("hello")
```

## Common Mistakes

```python
# WRONG: Not using context manager for files
f = open("file.txt")
data = f.read()
f.close()  # Never reached if read() raises!

# CORRECT: Use with statement
with open("file.txt") as f:
    data = f.read()

# WRONG: Catching exceptions in the context manager body incorrectly
@contextmanager
def bad_manager():
    try:
        yield
    except Exception:
        pass  # Silently swallows exceptions!

# CORRECT: Let exceptions propagate or handle explicitly
@contextmanager
def good_manager():
    try:
        yield
    except Exception:
        # Log or cleanup, then re-raise
        print("Error occurred")
        raise

# WRONG: Using yield in a finally block
@contextmanager
def broken():
    yield  # Code after yield never runs if exception occurs!
    cleanup()

# CORRECT: Use try/finally around yield
@contextmanager
def correct():
    try:
        yield
    finally:
        cleanup()  # Always runs
```

## Gotchas
- `@contextmanager` function must have exactly one `yield`
- Code before `yield` is `__enter__`, code after is `__exit__`
- If the `with` block raises, the exception appears at the `yield` point
- Use `try/finally` around `yield` to ensure cleanup happens
- `contextlib.suppress(Exception)` is a cleaner way to ignore specific exceptions
- `contextlib.asynccontextmanager` for async context managers
- `ExitStack` manages a dynamic number of context managers

## Related
- python/stdlib/asyncio-basics.md
- python/db/sqlalchemy-2.0/models.md
