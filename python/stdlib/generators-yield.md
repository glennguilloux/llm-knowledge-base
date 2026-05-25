---
id: "python-stdlib-generators-yield"
title: "Generators and the yield Keyword"
language: "python"
category: "stdlib"
tags: ["generators", "yield", "iterator", "lazy-evaluation", "memory", "coroutine"]
version: "3.10+"
retrieval_hint: "generator yield iterator lazy evaluation memory efficient sequence"
last_verified: "2026-05-24"
confidence: "high"
---

# Generators and the yield Keyword

## When to Use
- Processing large datasets that don't fit in memory
- Building pipelines that process data incrementally
- Replacing lists with lazy sequences for performance
- Implementing custom iteration logic without building a full class
- Streaming data from files, network, or sensors

## Standard Pattern

```python
from typing import Generator, Iterator
import sys


def fibonacci(limit: int) -> Generator[int, None, None]:
    """Generate Fibonacci numbers up to limit."""
    a, b = 0, 1
    while a <= limit:
        yield a
        a, b = b, a + b


def read_lines(filepath: str) -> Generator[str, None, None]:
    """Lazily read a file line by line without loading it all into memory."""
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            yield line.strip()


def chunked(data: list, size: int) -> Generator[list, None, None]:
    """Yield successive chunks from a list."""
    if size <= 0:
        raise ValueError("Chunk size must be positive")
    for i in range(0, len(data), size):
        yield data[i:i + size]


def pipeline(data: Iterator[int]) -> Generator[int, None, None]:
    """Chain generator operations into a pipeline."""
    for item in data:
        if item % 2 == 0:
            yield item * 2


# Using send() for two-way communication
def running_average() -> Generator[float, float, None]:
    """Coroutine that computes a running average."""
    total = 0.0
    count = 0
    while True:
        value = yield (total / count if count else 0.0)
        if value is None:
            break
        total += value
        count += 1


# Usage
if __name__ == "__main__":
    # Basic generator
    for num in fibonacci(100):
        print(num, end=" ")
    print()

    # Generator expression (inline)
    squares = (x * x for x in range(10))
    print(f"Generator object: {squares}")
    print(f"Size: {sys.getsizeof(squares)} bytes")

    # List equivalent for comparison
    squares_list = [x * x for x in range(10)]
    print(f"List size: {sys.getsizeof(squares_list)} bytes")

    # Chunked processing
    data = list(range(10))
    for c in chunked(data, 3):
        print(c)

    # Coroutine with send()
    avg = running_average()
    next(avg)  # Prime the coroutine
    print(avg.send(10))  # 10.0
    print(avg.send(20))  # 15.0
    print(avg.send(30))  # 20.0
    avg.close()
```

## Common Mistakes

```python
# WRONG: Trying to reuse a generator after exhaustion
def get_numbers():
    yield 1
    yield 2
    yield 3

gen = get_numbers()
print(list(gen))  # [1, 2, 3]
print(list(gen))  # [] — generator is exhausted!

# CORRECT: Create a new generator or use a function that returns one
def get_numbers():
    yield 1
    yield 2
    yield 3

print(list(get_numbers()))  # [1, 2, 3]
print(list(get_numbers()))  # [1, 2, 3] — fresh generator each call

# WRONG: Using return with a value inside a generator (pre-PEP 380)
def bad_generator():
    yield 1
    return 42  # In Python <3.3, this raises SyntaxError

# CORRECT: Use return to signal end; value is in StopIteration.value
def good_generator():
    yield 1
    yield 2
    return 42  # Python 3.3+ — value accessible via StopIteration

# WRONG: Forgetting to prime a coroutine before sending
def accumulator():
    total = 0
    while True:
        value = yield total
        total += value

acc = accumulator()
acc.send(10)  # TypeError: can't send non-None value to a just-started generator

# CORRECT: Prime with next() or send(None) first
acc = accumulator()
next(acc)       # Prime it — advances to first yield
print(acc.send(10))  # 10
print(acc.send(5))   # 15

# WRONG: Using a generator where random access is needed
def gen():
    for i in range(100):
        yield i

g = gen()
print(g[5])  # TypeError: 'generator' object is not subscriptable

# CORRECT: Convert to list if you need indexing, or use itertools.islice
g = gen()
from itertools import islice
print(next(islice(g, 5, 6)))  # 5
```

## Gotchas
- Generators are single-use — once exhausted, they yield nothing; create a new one or use a factory function
- `yield` turns a function into a generator function; calling it returns a generator object, it doesn't execute the body immediately
- Generator expressions `(x for x in ...)` are memory-efficient but can only be iterated once
- `send()` cannot be used on a fresh coroutine — you must prime it with `next()` or `send(None)` first
- Generators don't have a `len()` — use `sum(1 for _ in gen)` to count (but this exhausts the generator)
- `yield from` delegates to a sub-generator and forwards `send()` and `throw()` calls
- A `return` value inside a generator is NOT yielded — it's stored in `StopIteration.value`
- `itertools.tee()` can split a generator into N independent iterators, but it caches values in memory

## Related
- python/stdlib/context-managers.md
- python/stdlib/concurrency-choices.md
