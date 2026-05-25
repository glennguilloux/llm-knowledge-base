---
id: "python-stdlib-variables-scope"
title: "Variable Scope and the LEGB Rule"
language: "python"
category: "stdlib"
tags: ["scope", "LEGB", "global", "nonlocal", "closure", "namespace", "binding"]
version: "3.10+"
retrieval_hint: "scope LEGB global nonlocal closure namespace variable binding"
last_verified: "2026-05-24"
confidence: "high"
---

# Variable Scope and the LEGB Rule

## When to Use
- Understanding which variable a name refers to in nested functions
- Fixing `UnboundLocalError` when assigning to a variable that shadows an outer one
- Creating closures that capture and mutate outer state with `nonlocal`
- Modifying module-level globals with `global`
- Avoiding mutable default argument traps

## Standard Pattern

```python
from typing import Callable


# LEGB: Local -> Enclosing -> Global -> Built-in
counter: int = 0  # Global scope


def demonstrate_legb() -> None:
    """Show how Python resolves variable names."""
    counter: int = 10  # Enclosing scope

    def inner() -> None:
        counter: int = 20  # Local scope
        print(f"Local: {counter}")        # 20

    inner()
    print(f"Enclosing: {counter}")        # 10 (unchanged)


def use_global() -> None:
    """Modify a global variable from within a function."""
    global counter
    counter += 1
    print(f"Global counter: {counter}")


def make_counter() -> Callable[[], int]:
    """Closure with mutable state using nonlocal."""
    count: int = 0

    def increment() -> int:
        nonlocal count
        count += 1
        return count

    return increment


def accumulator(start: int = 0) -> Callable[[int], int]:
    """Create an accumulator closure with initial value."""
    total: int = start

    def add(value: int = 0) -> int:
        nonlocal total
        total += value
        return total

    return add


def resettable_counter() -> tuple[Callable[[], int], Callable[[], None]]:
    """Return increment and reset functions sharing state."""
    count: int = 0

    def increment() -> int:
        nonlocal count
        count += 1
        return count

    def reset() -> None:
        nonlocal count
        count = 0

    return increment, reset


# Example usage
if __name__ == "__main__":
    demonstrate_legb()
    # Local: 20
    # Enclosing: 10

    use_global()  # Global counter: 1
    use_global()  # Global counter: 2

    counter_fn: Callable[[], int] = make_counter()
    print(counter_fn())  # 1
    print(counter_fn())  # 2
    print(counter_fn())  # 3

    acc: Callable[[int], int] = accumulator(100)
    print(acc(5))   # 105
    print(acc(10))  # 115

    inc, reset = resettable_counter()
    print(inc())   # 1
    print(inc())   # 2
    reset()
    print(inc())   # 1
```

## Common Mistakes

```python
# WRONG: UnboundLocalError from assigning to a variable in inner scope
total: int = 0


def broken_increment(value: int) -> int:
    total = total + value  # UnboundLocalError: local variable referenced before assignment
    return total

# CORRECT: Declare nonlocal (or global) before assignment
def fixed_increment(value: int) -> int:
    global total
    total = total + value
    return total

# WRONG: Using mutable default argument (shared across calls)
def append_item(item: str, items: list[str] = []) -> list[str]:
    items.append(item)
    return items

print(append_item("a"))  # ['a']
print(append_item("b"))  # ['a', 'b'] — default list was mutated!

# CORRECT: Use None as default, create new list inside
def append_item_safe(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items

print(append_item_safe("a"))  # ['a']
print(append_item_safe("b"))  # ['b'] — fresh list each time

# WRONG: Late binding in closures within a loop
def make_functions_wrong() -> list[Callable[[], int]]:
    functions: list[Callable[[], int]] = []
    for i in range(3):
        functions.append(lambda: i)  # All capture the same `i`
    return functions

fns_wrong = make_functions_wrong()
print([f() for f in fns_wrong])  # [2, 2, 2] — not [0, 1, 2]!

# CORRECT: Bind loop variable as default argument
def make_functions_correct() -> list[Callable[[], int]]:
    functions: list[Callable[[], int]] = []
    for i in range(3):
        functions.append(lambda i=i: i)  # Captures current value of i
    return functions

fns_correct = make_functions_correct()
print([f() for f in fns_correct])  # [0, 1, 2]

# WRONG: Confusing global with enclosing (nonlocal)
def outer() -> None:
    x: int = 10

    def inner() -> None:
        global x  # Tries to make x refer to module-level x, not outer's x!
        x = 20

    inner()
    print(x)  # 10 — outer x unchanged

# CORRECT: Use nonlocal for enclosing scope
def outer_fixed() -> None:
    x: int = 10

    def inner() -> None:
        nonlocal x
        x = 20

    inner()
    print(x)  # 20 — outer x modified
```

## Gotchas
- Python's scoping follows **LEGB**: Local -> Enclosing -> Global -> Built-in
- Assignment inside a function makes a variable **local** to that scope — even if an outer scope has the same name
- `global` binds to the **module-level** namespace; `nonlocal` binds to the nearest **enclosing** (non-global) scope
- Mutable default arguments (`def f(x=[])`) are **created once at function definition time** and shared across all calls
- Closures in loops capture the **variable itself**, not its value — this is late binding
- `nonlocal` cannot find global variables — it only looks in enclosing scopes
- Class body scope is **special**: variables defined in a class body are not accessible in nested class scopes via `nonlocal`
- `dir()` and `globals()` / `locals()` can inspect the current namespace dictionaries
- The `:=` walrus operator (3.8+) creates variables in the **enclosing** scope, not a new scope

## Related
- python/stdlib/decorators.md
- python/stdlib/context-managers.md
- python/stdlib/generators-yield.md
