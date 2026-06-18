---
id: "python-stdlib-match-case"
title: "Structural Pattern Matching (match/case) in Python 3.10+"
language: "python"
category: "stdlib"
subcategory: "control-flow"
tags: ["match", "case", "pattern-matching", "structural", "python3.10", "destructuring"]
version: "3.10+"
retrieval_hint: "Python match case structural pattern matching destructuring guard wildcard"
last_verified: "2026-05-25"
confidence: "high"
---

# Structural Pattern Matching (match/case) in Python 3.10+

## When to Use
- Replacing long if/elif chains that check type, shape, or value
- Destructuring nested data structures (JSON, tuples, dataclasses, dicts)
- Writing readable dispatch logic based on object type and attributes
- Parsing ASTs, protocol messages, or command-line arguments

## Standard Pattern

```python
from dataclasses import dataclass
from typing import Any


# --- Literal and Capture Patterns ---
def describe_value(val: Any) -> str:
    match val:
        case 0:
            return "Zero"
        case 1 | 2 | 3:
            return "Small number"
        case True:
            return "Boolean True"
        case None:
            return "Nothing"
        case str():
            return f"A string: {val}"
        case _:
            return f"Something else: {type(val).__name__}"


# --- Sequence Pattern Matching ---
def process_command(cmd: list[str]) -> str:
    match cmd:
        case ["quit"]:
            return "Quitting"
        case ["load", filename]:
            return f"Loading {filename}"
        case ["save", filename, *rest] if rest:  # Guard
            return f"Saving {filename} with options: {rest}"
        case ["save", filename]:
            return f"Saving {filename}"
        case _:
            return f"Unknown: {cmd}"


# --- Mapping Pattern Matching ---
def handle_api_response(response: dict) -> str:
    match response:
        case {"status": 200, "data": data}:
            return f"Success: {data}"
        case {"status": 404}:
            return "Not found"
        case {"status": code, "error": msg}:
            return f"Error {code}: {msg}"
        case _:
            return "Unknown response format"


# --- Class/Instance Pattern Matching ---
@dataclass
class Point:
    x: float
    y: float

@dataclass
class Circle:
    center: Point
    radius: float

@dataclass
class Rectangle:
    top_left: Point
    bottom_right: Point

def describe_shape(shape: Any) -> str:
    match shape:
        case Circle(center=Point(x=0, y=0), radius=r):
            return f"Circle at origin with radius {r}"
        case Circle(center=Point(x, y), radius=r):
            return f"Circle at ({x},{y}) with radius {r}"
        case Rectangle(Point(x1, y1), Point(x2, y2)):
            return f"Rectangle from ({x1},{y1}) to ({x2},{y2})"
        case _:
            return "Unknown shape"


# --- OR Pattern and Subpattern Matching ---
def handle_event(event: tuple) -> str:
    match event:
        case ("click", x, y) | ("tap", x, y):
            return f"Click/tap at ({x},{y})"
        case ("keypress", key) if key in "wasd":
            return f"Movement key: {key}"
        case ("keypress", key):
            return f"Key: {key}"
        case _:
            return f"Unknown event: {event[0] if event else 'empty'}"
```

## Common Mistakes

```python
# WRONG: Expecting fall-through between cases
# Unlike switch in C, match does NOT fall through
def wrong_fallthrough(val):
    match val:
        case 1:
            result = "one"
        case 2:
            result = "two"
    # This is fine — no fallthrough

# WRONG: Using _ as a variable name inside a case pattern
# _ is the wildcard — it matches anything but DOES NOT bind
match value:
    case [_, x]:  # _ is wildcard, not bound
        print(x)  # OK: x is bound
    # print(_)    # ERROR: _ is not bound

# WRONG: Capturing a value that shadows outer scope
SENSITIVE_VALUE = 42

def check(val):
    match val:
        case SENSITIVE_VALUE:  # This is a CAPTURE pattern, not a comparison!
            return "Matched the constant"
        case _:
            return "No match"

# This matches ANY value and binds it to SENSITIVE_VALUE!
# It does NOT compare against the constant 42

# CORRECT: Use a guard for constant comparison
def check_correct(val):
    match val:
        case x if x == SENSITIVE_VALUE:  # Guard compares
            return f"Got the sensitive value: {x}"
        case _:
            return "No match"

# CORRECT: Use dotted constant (Python 3.11+)
from mymodule import MY_CONSTANT

match val:
    case MY_CONSTANT:  # Dotted name = constant pattern (no capture)
        return "Matched constant"

# WRONG: Using match for simple if/elif scenarios
# match is overkill for simple value comparisons
match status_code:
    case 200:
        handle_ok()
    case 404:
        handle_not_found()

# CORRECT: Simpler if/elif is fine for simple cases
if status_code == 200:
    handle_ok()
elif status_code == 404:
    handle_not_found()
```

## Gotchas
- **Variable capture vs constants:** Inside a `case` block, any bare name is a *capture pattern* — it matches everything and binds the value. To match against a constant, use a dotted name (`module.CONSTANT`) or a guard (`case x if x == CONSTANT`). This is the #1 source of match/case bugs.
- **Wildcard `_` is not bound:** The wildcard `_` matches anything but does NOT bind. You cannot reference `_` after the pattern. If you need to bind but ignore, use a name like `_unused` or `ignored`.
- **OR patterns bind consistently:** In `case 1 | 2 | 3:`, you cannot capture different variables across alternatives. `case [x] | {"key": x}:` is valid (same variable), but `case [x] | {"key": y}:` is a syntax error.
- **Sequence vs iterable:** Match only destructures sequences (list, tuple, range, memoryview, array.array). Generators, sets, and custom iterables are NOT matched by sequence patterns — they'll fall through to `_`.
- **Guard evaluation timing:** Guards (`case pattern if condition:`) are evaluated AFTER the pattern matches. The condition can use captured variables. If the guard raises, it's treated as a failed match (not an error) and falls through to the next case.

## Related
- python/stdlib/dataclasses.md
- python/data/pydantic-v2/computed-validators.md
