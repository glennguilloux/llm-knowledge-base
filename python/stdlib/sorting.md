---
id: "python-stdlib-sorting"
title: "Sorting with list.sort() and sorted()"
language: "python"
category: "stdlib"
tags: ["sorting", "sort", "sorted", "key", "cmp", "functools", "cmp_to_key", "order"]
version: "3.10+"
retrieval_hint: "sort sorted key cmp_to_key ordering list sort reverse stable"
last_verified: "2026-05-24"
confidence: "high"
---

# Sorting with list.sort() and sorted()

## When to Use
- Ordering a list in-place without creating a copy (`list.sort()`)
- Producing a new sorted iterable without modifying the original (`sorted()`)
- Sorting by a derived key (e.g., attribute, computed value)
- Multi-level / compound sorting (sort by one key, then by another)
- Custom ordering logic beyond natural order

## Standard Pattern

```python
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Employee:
    name: str
    department: str
    salary: int
    hire_date: str  # ISO 8601 "YYYY-MM-DD"


def sort_by_key(data: list[dict[str, Any]], key: str, reverse: bool = False) -> list[dict[str, Any]]:
    """Return a new list sorted by a given key. Original list is unmodified."""
    return sorted(data, key=lambda item: item[key], reverse=reverse)


def sort_in_place(data: list[int]) -> None:
    """Sort a list in place — mutates the original, no copy made."""
    data.sort()


def sort_by_multiple_keys(employees: list[Employee]) -> list[Employee]:
    """Sort by department first, then by salary descending within each department."""
    return sorted(employees, key=lambda e: (e.department, -e.salary))


def sort_by_attribute(objects: list[Any], attr: str, reverse: bool = False) -> list[Any]:
    """Sort objects by a named attribute using operator.attrgetter."""
    from operator import attrgetter
    return sorted(objects, key=attrgetter(attr), reverse=reverse)


def sort_with_custom_cmp(data: list[str]) -> list[str]:
    """Sort using a custom comparator function (rare — prefer key= when possible)."""
    import functools

    def compare(a: str, b: str) -> int:
        # Sort by length first, then alphabetically
        if len(a) != len(b):
            return -1 if len(a) < len(b) else 1
        if a < b:
            return -1
        if a > b:
            return 1
        return 0

    return sorted(data, key=functools.cmp_to_key(compare))


# Example usage
if __name__ == "__main__":
    employees: list[Employee] = [
        Employee("Alice", "Engineering", 120000, "2020-03-15"),
        Employee("Bob", "Marketing", 90000, "2019-07-01"),
        Employee("Charlie", "Engineering", 130000, "2018-01-10"),
        Employee("Diana", "Marketing", 95000, "2021-11-20"),
        Employee("Eve", "Engineering", 120000, "2022-06-01"),
    ]

    by_dept_then_salary: list[Employee] = sort_by_multiple_keys(employees)
    for emp in by_dept_then_salary:
        print(f"{emp.department:12s} {emp.salary:>7d} {emp.name}")

    strings: list[str] = ["banana", "apple", "cherry", "date"]
    by_custom: list[str] = sort_with_custom_cmp(strings)
    print(by_custom)  # ['date', 'apple', 'banana', 'cherry']
```

## Common Mistakes

```python
# WRONG: Assigning list.sort() result to a variable
numbers: list[int] = [3, 1, 4, 1, 5]
sorted_numbers: list[int] = numbers.sort()  # .sort() returns None!
print(sorted_numbers)  # None

# CORRECT: Use sorted() for a new list, or .sort() in place
sorted_numbers = sorted(numbers)      # new list
numbers.sort()                        # in-place, numbers is now sorted

# WRONG: Using a mutable default as sort key inadvertently
# Sorting by a lambda that captures a changing variable
items: list[list[int]] = [[3, 1], [1, 2], [2, 3]]
# This works but be careful with closures in loops
result = sorted(items, key=lambda x: x[0])  # OK

# WRONG: Sorting mixed types without a key
mixed: list[Any] = [3, "2", 1, "4"]
result = sorted(mixed)  # TypeError: '<' not supported between 'str' and 'int'

# CORRECT: Provide a key that produces comparable values
result = sorted(mixed, key=str)  # Sort all as strings

# WRONG: Using sort key that changes during sort (non-deterministic)
import random
data: list[dict[str, int]] = [{"val": 1}, {"val": 2}, {"val": 3}]
result = sorted(data, key=lambda x: random.random())  # Non-deterministic, unstable

# CORRECT: Use a stable, deterministic key
result = sorted(data, key=lambda x: x["val"])

# WRONG: Sorting case-sensitively when case-insensitive is intended
words: list[str] = ["banana", "Apple", "cherry", "Date"]
result = sorted(words)
print(result)  # ['Apple', 'Date', 'banana', 'cherry'] — uppercase comes first!

# CORRECT: Use str.lower as the key
result = sorted(words, key=str.lower)
print(result)  # ['Apple', 'banana', 'cherry', 'Date']
```

## Gotchas
- Python's sort is **stable** — equal elements keep their relative order. This means you can sort by multiple criteria by doing multiple sorts in reverse order of priority
- `list.sort()` is slightly faster than `sorted()` because it doesn't create a copy — use it when you don't need the original
- `sorted()` works on **any iterable**, not just lists: tuples, sets, dicts, generators
- When sorting dicts, `sorted(my_dict)` sorts the **keys**
- `operator.itemgetter` and `operator.attrgetter` are faster than equivalent `lambda` for simple key extraction
- For case-insensitive sorting of non-English text, use `locale.strxfrm` or `pyuca` instead of `str.lower`
- Python uses **Timsort** (a hybrid merge sort / insertion sort) — O(n log n) worst case, O(n) best case when data is nearly sorted
- `functools.cmp_to_key` converts an old-style comparison function to a key function, but it adds overhead — rewrite as `key=` when possible
- Sorting `None` values: `None` cannot be compared with `int` in Python 3 — use a key like `key=lambda x: float('inf') if x is None else x`

## Related
- python/stdlib/decorators.md
- python/stdlib/generators-yield.md
