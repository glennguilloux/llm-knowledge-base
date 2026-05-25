---
id: "python-stdlib-slicing"
title: "Sequence Slicing and Extended Slices"
language: "python"
category: "stdlib"
tags: ["slicing", "slice", "sequence", "list", "str", "indexing", "stride"]
version: "3.10+"
retrieval_hint: "slicing slice sequence list string index stride extended slice"
last_verified: "2026-05-24"
confidence: "high"
---

# Sequence Slicing and Extended Slices

## When to Use
- Extracting sub-sequences from lists, strings, tuples without loops
- Reversing sequences with a simple notation
- Skipping elements with stride/step values
- Cloning lists (shallow copy) safely
- Implementing `__getitem__` to support slicing on custom classes

## Standard Pattern

```python
from typing import Any


# Basic slicing: seq[start:stop:step]
data = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# Common operations
first_three = data[:3]       # [0, 1, 2]
last_three = data[-3:]       # [7, 8, 9]
middle = data[3:7]           # [3, 4, 5, 6]
every_other = data[::2]      # [0, 2, 4, 6, 8]
reversed_data = data[::-1]   # [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]

# Shallow copy (safer than assignment which creates an alias)
copy = data[:]
assert copy == data
assert copy is not data  # Different objects

# Slice assignment (replace a section)
data[2:5] = [20, 30, 40]
print(data)  # [0, 1, 20, 30, 40, 5, 6, 7, 8, 9]

# Slice deletion
data = [0, 1, 2, 3, 4, 5]
del data[2:4]
print(data)  # [0, 1, 4, 5]

# Slice assignment with different length (grows/shrinks list)
data = [1, 2, 3]
data[1:2] = [10, 20, 30]
print(data)  # [1, 10, 20, 30, 3]

# Using slice objects programmatically
items = slice(1, 5, 2)  # start=1, stop=5, step=2
print(data[items])  # [10, 30]

# Custom class supporting slicing
class RingBuffer:
    """A fixed-size ring buffer that supports slicing."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.buffer: list[Any] = []

    def append(self, item: Any) -> None:
        if len(self.buffer) >= self.capacity:
            self.buffer.pop(0)
        self.buffer.append(item)

    def __getitem__(self, index: Any) -> Any:
        if isinstance(index, slice):
            return self.buffer[index]
        return self.buffer[index]

    def __len__(self) -> int:
        return len(self.buffer)

    def __repr__(self) -> str:
        return f"RingBuffer({self.buffer})"


# String slicing
text = "Hello, World!"
print(text[7:12])    # "World"
text_reversed = text[::-1]  # "!dlroW ,olleH"

# Negative indices
print(data[-1])    # Last element
print(data[-2:])   # Last two elements
```

## Common Mistakes

```python
# WRONG: Thinking slicing raises IndexError for out-of-bounds
data = [1, 2, 3]
print(data[0:100])   # [1, 2, 3] — no error, just returns what's available
print(data[50:100])  # [] — empty, no error

# CORRECT: Slicing is safe — it clamps to valid range
# Use direct indexing if you want IndexError for bounds checking
print(data[100])  # IndexError: list index out of range

# WRONG: Modifying a list while iterating over a slice copy
data = [1, 2, 3, 4, 5]
for item in data[:]:  # Iterating over a copy
    if item % 2 == 0:
        data.remove(item)  # Modifying original — this works because we iterate the copy
print(data)  # [1, 3, 5]

# But this is WRONG:
data = [1, 2, 3, 4, 5]
for item in data:  # Iterating over original
    if item % 2 == 0:
        data.remove(item)  # Skips elements!
print(data)  # [1, 3, 5] — seems OK but try with [2, 4, 6]

data = [2, 4, 6]
for item in data:
    data.remove(item)
print(data)  # [4] — BUG! Elements skipped during iteration

# CORRECT: Use a copy for iteration
data = [2, 4, 6]
for item in data[:]:
    data.remove(item)
print(data)  # []

# WRONG: Assuming slice assignment replaces in-place (it doesn't always)
data = [1, 2, 3, 4, 5]
original_id = id(data)
data[1:3] = [10, 20, 30, 40]  # List grows!
print(id(data) == original_id)  # True — same object, but length changed
print(data)  # [1, 10, 20, 30, 40, 4, 5]

# CORRECT: Understand that slice assignment can change the list length
# If you need fixed-size replacement, ensure the replacement matches the slice length

# WRONG: Using stride with start/stop in unexpected ways
data = [0, 1, 2, 3, 4, 5]
print(data[5:0:-1])  # [5, 4, 3, 2, 1] — stops BEFORE index 0
print(data[5:0:-2])  # [5, 3, 1]

# CORRECT: With negative step, start should be > stop
print(data[5::-1])   # [5, 4, 3, 2, 1, 0] — includes index 0
```

## Gotchas
- Slicing never raises `IndexError` — out-of-bounds slices return what's available or an empty sequence
- `seq[:]` creates a SHALLOW copy — nested objects are still shared references
- `seq[::-1]` is the idiomatic way to reverse a sequence; it creates a new object
- Slice assignment can change the list length — the replacement doesn't need to match the slice size
- With a negative step, the start index must be greater than the stop index, or you get an empty result
- `slice(start, stop, step)` objects can be created independently and reused across sequences
- Strings are immutable, so string slicing always creates a new string — there's no slice assignment
- `slice.indices(len)` normalizes a slice for a given length, handling `None` and negative values

## Related
- python/stdlib/file-io.md
- python/stdlib/typing-advanced.md
