---
id: "python-stdlib-flatten-lists"
title: "Flattening Nested Lists"
language: "python"
category: "stdlib"
tags: ["flatten", "nested", "list", "itertools", "chain", "comprehension"]
version: "3.10+"
retrieval_hint: "flatten nested list itertools chain comprehension recursive"
last_verified: "2026-05-24"
confidence: "high"
---

# Flattening Nested Lists

## When to Use
- Converting a list of lists into a single flat list
- Processing nested data structures (JSON, tree results)
- Preparing data for batch operations
- Flattening one level vs recursive deep flattening

## Standard Pattern

```python
from itertools import chain
from collections.abc import Iterable
from typing import Any


# --- One-level flatten ---

# List comprehension (most Pythonic for one level)
nested = [[1, 2, 3], [4, 5], [6, 7, 8]]
flat = [item for sublist in nested for item in sublist]
# [1, 2, 3, 4, 5, 6, 7, 8]

# itertools.chain (memory efficient — returns iterator)
flat_iter = chain.from_iterable(nested)
flat_list = list(flat_iter)
# [1, 2, 3, 4, 5, 6, 7, 8]

# chain with individual lists
flat = list(chain([1, 2], [3, 4], [5, 6]))
# [1, 2, 3, 4, 5, 6]


# --- Recursive deep flatten ---

def flatten_deep(items: Iterable[Any]) -> list[Any]:
    """Recursively flatten any nesting depth."""
    result: list[Any] = []
    for item in items:
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
            result.extend(flatten_deep(item))
        else:
            result.append(item)
    return result

deep = [1, [2, [3, [4, 5]]], 6, [[7], 8]]
flat = flatten_deep(deep)
# [1, 2, 3, 4, 5, 6, 7, 8]


# --- Generator version (memory efficient) ---

def flatten_deep_gen(items: Iterable[Any]):
    """Generator that yields items from arbitrarily nested iterables."""
    for item in items:
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
            yield from flatten_deep_gen(item)
        else:
            yield item

flat = list(flatten_deep_gen([1, [2, [3, [4]]]]))
# [1, 2, 3, 4]


# --- Flatten with numpy (for numeric data) ---

import numpy as np

nested = [[1, 2, 3], [4, 5, 6]]
arr = np.array(nested)
flat = arr.flatten()        # Returns copy: array([1, 2, 3, 4, 5, 6])
flat_ravel = arr.ravel()    # Returns view when possible (faster)


# --- Flatten dict of lists ---

data = {"a": [1, 2], "b": [3, 4], "c": [5, 6]}
all_values = list(chain.from_iterable(data.values()))
# [1, 2, 3, 4, 5, 6]


# --- Flatten with mixed types ---

def flatten_safe(items: Iterable[Any]) -> list[Any]:
    """Flatten, treating strings as atomic (not iterable)."""
    result: list[Any] = []
    for item in items:
        if isinstance(item, list):
            result.extend(flatten_safe(item))
        else:
            result.append(item)
    return result

mixed = ["hello", ["world", ["!"]], 42, [3.14]]
flat = flatten_safe(mixed)
# ["hello", "world", "!", 42, 3.14]
```

## Common Mistakes

```python
# WRONG: sum() to flatten (O(n^2) — very slow for large lists)
nested = [[1, 2], [3, 4], [5, 6]]
flat = sum(nested, [])  # Works but O(n^2)!

# CORRECT: Use list comprehension or chain
flat = [item for sublist in nested for item in sublist]
# or
flat = list(chain.from_iterable(nested))

# WRONG: Recursive flatten that treats strings as iterable
def bad_flatten(items):
    result = []
    for item in items:
        if isinstance(item, Iterable):
            result.extend(bad_flatten(item))  # Strings are iterable!
        else:
            result.append(item)
    return result

bad_flatten(["hello", ["world"]])
# ['h', 'e', 'l', 'l', 'o', 'w', 'o', 'r', 'l', 'd']  # Oops!

# CORRECT: Exclude str and bytes from iteration check
def good_flatten(items):
    result = []
    for item in items:
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
            result.extend(good_flatten(item))
        else:
            result.append(item)
    return result

# WRONG: Modifying list while iterating to flatten
nested = [[1, 2], [3, 4]]
for sublist in nested:
    for item in sublist:
        nested.append(item)  # Infinite loop!

# CORRECT: Build a new list
flat = [item for sublist in nested for item in sublist]

# WRONG: Assuming chain returns a list
result = chain.from_iterable([[1, 2], [3, 4]])
print(result[0])  # TypeError: 'chain' object is not subscriptable

# CORRECT: Convert to list first
result = list(chain.from_iterable([[1, 2], [3, 4]]))
print(result[0])  # 1
```

## Gotchas
- `sum(list_of_lists, [])` works but is O(n²) — each `+` creates a new list. Never use for large data
- `chain.from_iterable()` returns an iterator — wrap in `list()` if you need indexing or length
- Strings are iterable in Python — recursive flatteners must explicitly exclude `str` and `bytes`
- `yield from` delegates to a sub-generator — use it in recursive generators for clean code
- `numpy.flatten()` always returns a copy; `numpy.ravel()` returns a view when possible (faster, less memory)
- For deeply nested structures, recursive flatteners may hit Python's recursion limit (default 1000)
- `more_itertools.collapse()` is a battle-tested third-party recursive flattener
- List comprehension flatten `[x for sub in nested for x in sub]` reads left-to-right like nested loops

## Related
- python/stdlib/generators-yield.md
- python/stdlib/slicing.md
- python/stdlib/enumerate-zip.md
