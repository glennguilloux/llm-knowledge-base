---
id: "python-stdlib-main-guard"
title: "The if __name__ == '__main__' Guard"
language: "python"
category: "stdlib"
tags: ["main-guard", "entry-point", "module", "import", "script", "dunder"]
version: "3.10+"
retrieval_hint: "if name main entry point module import script guard"
last_verified: "2026-05-24"
confidence: "high"
---

# The if __name__ == '__main__' Guard

## When to Use
- Writing modules that can be both imported and run as scripts
- Preventing test/demo code from executing on import
- Defining a clear entry point for a Python package
- Running CLI tools that are also importable libraries
- Executing tests or benchmarks when a file is run directly

## Standard Pattern

```python
#!/usr/bin/env python3
"""Module that can be imported or run as a script."""

from __future__ import annotations

import argparse
import sys
from typing import Optional


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Calculator CLI")
    parser.add_argument("a", type=float, help="First number")
    parser.add_argument("b", type=float, help="Second number")
    parser.add_argument(
        "--operation",
        choices=["add", "multiply"],
        default="add",
        help="Operation to perform",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point."""
    args = parse_args(argv)
    if args.operation == "add":
        result = add(args.a, args.b)
    else:
        result = multiply(args.a, args.b)
    print(f"{args.a} {args.operation} {args.b} = {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## Common Mistakes

```python
# WRONG: Code at module level runs on import
# calculator.py
print("Initializing calculator...")  # Runs when imported!
result = add(1, 2)  # Side effects on import!

# CORRECT: Guard all executable code
def main():
    print("Initializing calculator...")
    result = add(1, 2)
    return result

if __name__ == "__main__":
    main()

# WRONG: Using a bare string comparison without quotes
if __name__ == "__main__":  # This is actually correct
    pass

if __name__ == __main__:  # NameError: name '__main__' is not defined
    pass

# CORRECT: Always compare against the string "__main__"
if __name__ == "__main__":
    main()

# WRONG: Putting logic directly in the guard block (hard to test)
if __name__ == "__main__":
    import sys
    x = int(sys.argv[1])
    y = int(sys.argv[2])
    print(x + y)
    # No way to call this programmatically!

# CORRECT: Wrap logic in a function, guard just calls it
def main(argv=None):
    import argparse
    args = parse_args(argv)
    print(args.a + args.b)
    return 0

if __name__ == "__main__":
    sys.exit(main())

# WRONG: Forgetting sys.exit() — the script always exits 0
if __name__ == "__main__":
    main()  # If main returns non-zero, exit code is still 0

# CORRECT: Propagate the return code
if __name__ == "__main__":
    sys.exit(main())
```

## Gotchas
- `__name__` is `"__main__"` only when the file is run directly; when imported, it's the module's dotted path (e.g., `"calculator"`)
- The guard is NOT the same as a C `main()` function — Python runs top-to-bottom, so all definitions (functions, classes) execute before the guard
- `sys.exit()` inside the guard prevents accidental use as a script when imported; without it, the return value of `main()` is silently ignored
- For packages, `__main__.py` serves as the entry point when running `python -m package_name`
- `argparse` should be called inside a function (not at module level) so the module can be imported without side effects
- The `from __future__ import annotations` import must come before any other code (except the shebang or docstring)
- Test frameworks like `pytest` import your modules — code outside the guard will run during test collection

## Related
- python/stdlib/cli-argparse.md
- python/stdlib/decorators.md
