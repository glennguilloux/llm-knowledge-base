---
id: "python-stdlib-enumerate-zip"
title: "Iteration Helpers: enumerate() and zip()"
language: "python"
category: "stdlib"
tags: ["enumerate", "zip", "iteration", "loop", "index", "strict", "unzip"]
version: "3.10+"
retrieval_hint: "enumerate zip iteration loop index strict unzip unpack"
last_verified: "2026-05-24"
confidence: "high"
---

# Iteration Helpers: enumerate() and zip()

## When to Use
- Need both the index and value when looping over a sequence (`enumerate`)
- Iterate over two or more sequences in parallel (`zip`)
- Build dicts or apply functions across paired sequences
- Unpacking ("unzipping") a list of tuples back into separate sequences
- Catching length mismatches when zipping (`strict=True` in 3.10+)

## Standard Pattern

```python
from itertools import zip_longest


def loop_with_index(items: list[str]) -> None:
    """Use enumerate to get both index and item in a loop."""
    for index, item in enumerate(items, start=1):
        print(f"{index}: {item}")


def zip_even_lengths(list_a: list[int], list_b: list[str]) -> list[tuple[int, str]]:
    """Zip two lists of equal length — raises ValueError if lengths differ (3.10+)."""
    result: list[tuple[int, str]] = []
    for num, text in zip(list_a, list_b, strict=True):
        result.append((num, text))
    return result


def zip_padded(list_a: list[int], list_b: list[str], fillvalue: str = "N/A") -> list[tuple[int, str]]:
    """Zip with padding for unequal lengths using itertools.zip_longest."""
    return list(zip_longest(list_a, list_b, fillvalue=fillvalue))


def unzip(pairs: list[tuple[str, int]]) -> tuple[list[str], list[int]]:
    """Unzip a list of tuples into separate lists."""
    names, scores = zip(*pairs)  # Returns tuples
    return list(names), list(scores)


def build_dict_from_lists(keys: list[str], values: list[int]) -> dict[str, int]:
    """Build a dict by zipping two lists together."""
    return dict(zip(keys, values))


def zip_three_or_more(*iterables):
    """Zip three or more iterables together."""
    results: list[tuple] = []
    for items in zip(*iterables, strict=True):
        results.append(items)
    return results


# Example usage
if __name__ == "__main__":
    fruits: list[str] = ["apple", "banana", "cherry"]
    loop_with_index(fruits)
    # 1: apple
    # 2: banana
    # 3: cherry

    numbers: list[int] = [1, 2, 3]
    colors: list[str] = ["red", "yellow", "red"]
    pairs: list[tuple[int, str]] = zip_even_lengths(numbers, colors)
    print(pairs)  # [(1, 'red'), (2, 'yellow'), (3, 'red')]

    # Unequal zipping with padding
    a: list[int] = [1, 2, 3, 4]
    b: list[str] = ["a", "b"]
    padded: list[tuple[int, str]] = zip_padded(a, b, fillvalue="?")
    print(padded)  # [(1, 'a'), (2, 'b'), (3, '?'), (4, '?')]

    # Dict from zipped lists
    ages: dict[str, int] = build_dict_from_lists(["Alice", "Bob"], [30, 25])
    print(ages)  # {'Alice': 30, 'Bob': 25}

    # Unzip
    scores: list[tuple[str, int]] = [("Alice", 95), ("Bob", 87), ("Charlie", 92)]
    names, vals = unzip(scores)
    print(names)  # ['Alice', 'Bob', 'Charlie']
    print(vals)   # [95, 87, 92]
```

## Common Mistakes

```python
# WRONG: Using range(len(...)) instead of enumerate
items: list[str] = ["a", "b", "c"]
for i in range(len(items)):
    print(i, items[i])  # Works but not Pythonic

# CORRECT: Use enumerate directly
for i, item in enumerate(items):
    print(i, item)

# WRONG: Forgetting stop when using range(1, len) for 1-based indexing
for i in range(1, len(items)):
    print(i, items[i])  # Skips index 0 item

# CORRECT: Use enumerate(..., start=1)
for i, item in enumerate(items, start=1):
    print(i, item)

# WRONG: Zipping lists of different length silently truncates
a: list[int] = [1, 2, 3, 4, 5]
b: list[str] = ["a", "b"]
result = list(zip(a, b))
print(result)  # [(1, 'a'), (2, 'b')] — silently drops 1, 2, 3!

# CORRECT: Use strict=True (3.10+) to catch mismatches
result = list(zip(a, b, strict=True))  # ValueError: zip() has arguments with different lengths

# WRONG: Converting zip object to list and reusing it
z = zip([1, 2, 3], ["a", "b", "c"])
print(list(z))  # [(1, 'a'), (2, 'b'), (3, 'c')]
print(list(z))  # [] — zip is an iterator, exhausted after one pass!

# CORRECT: Store as list if you need to iterate multiple times
z_list: list[tuple[int, str]] = list(zip([1, 2, 3], ["a", "b", "c"]))
print(z_list)  # [(1, 'a'), (2, 'b'), (3, 'c')]
print(z_list)  # [(1, 'a'), (2, 'b'), (3, 'c')]

# WRONG: Unzipping with zip(*pairs) but forgetting that it returns tuples
pairs: list[tuple[str, int]] = [("a", 1), ("b", 2)]
result = zip(*pairs)  # Iterator of tuples, not lists

# CORRECT: Convert to lists if needed
names, values = map(list, zip(*pairs))

# WRONG: Using zip when you need cartesian product
from itertools import product
result = zip([1, 2], [3, 4])  # [(1,3), (2,4)] — pairs, not all combinations

# CORRECT: Use itertools.product for cartesian product
result = list(product([1, 2], [3, 4]))  # [(1,3), (1,4), (2,3), (2,4)]
```

## Gotchas
- `enumerate` returns an iterator of `(index, item)` tuples — `start` parameter defaults to 0
- `zip` produces the **shortest** result by default; use `zip_longest` from `itertools` for longest with fill
- `zip` objects are **single-use iterators** — convert to list if you need to iterate multiple times
- `strict=True` (Python 3.10+) raises `ValueError` if iterables have different lengths — use it to catch bugs
- `zip(*matrix)` is the standard idiom to **transpose** a matrix (list of lists)
- `zip` can take any iterable as arguments — lists, tuples, sets, generators, strings
- `for i, x in enumerate(iterable)` is vastly more readable than `for i in range(len(iterable))` and should always be preferred
- `itertools.pairwise(iterable)` (3.10+) gives sliding pairs: `[(s0,s1), (s1,s2), ...]`
- When zipping strings, each character is an element: `zip("abc", "123")` yields `('a','1'), ('b','2'), ('c','3')`

## Related
- python/stdlib/slicing.md
- python/stdlib/generators-yield.md
- python/stdlib/typing-advanced.md
