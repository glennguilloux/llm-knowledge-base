---
id: "python-stdlib-pathlib"
title: "File Path Operations with pathlib"
language: "python"
category: "stdlib"
subcategory: "filesystem"
tags: ["pathlib", "path", "file", "directory", "filesystem"]
version: "3.10+"
retrieval_hint: "file path directory join resolve glob walk"
last_verified: "2026-05-24"
confidence: "high"
---

# File Path Operations with pathlib

## When to Use
- Building file paths in a cross-platform way
- Checking file/directory existence
- Reading/writing text or bytes to files
- Walking directory trees
- Globbing for files by pattern

## Standard Pattern

```python
from pathlib import Path

# Creating paths
home = Path.home()                    # /home/user
cwd = Path.cwd()                      # Current working directory
relative = Path("data") / "files"     # data/files
absolute = Path("/etc") / "hosts"     # /etc/hosts

# Path properties
p = Path("/home/user/document.txt")
p.name          # "document.txt"
p.stem          # "document"
p.suffix        # ".txt"
p.parent        # Path("/home/user")
p.parts         # ('/', 'home', 'user', 'document.txt')

# Existence checks
p.exists()      # True/False
p.is_file()     # True/False
p.is_dir()      # True/False

# Reading/writing
content = p.read_text(encoding="utf-8")
p.write_text("hello", encoding="utf-8")
data = p.read_bytes()
p.write_bytes(b"\x00\x01")

# Directory operations
p.mkdir(parents=True, exist_ok=True)  # Create with parents
list(p.iterdir())                      # List directory contents

# Globbing
list(Path(".").rglob("*.py"))          # Recursive glob
list(Path(".").glob("*.py"))           # Non-recursive glob

# Resolving paths
Path("./data/../file.txt").resolve()   # Absolute resolved path

# Renaming/moving
p.rename("new_name.txt")
p.unlink()                             # Delete file
```

## Common Mistakes

```python
# WRONG: Using os.path.join with pathlib
import os
os.path.join(Path("dir"), "file.txt")  # Mixes types

# CORRECT: Use / operator
Path("dir") / "file.txt"

# WRONG: String concatenation for paths
path = base_dir + "/" + filename  # Breaks on Windows

# CORRECT: Use pathlib
path = Path(base_dir) / filename

# WRONG: Not handling missing parent directories
Path("deep/nested/dir/file.txt").write_text("data")  # FileNotFoundError

# CORRECT: Create parents first
Path("deep/nested/dir/file.txt").parent.mkdir(parents=True, exist_ok=True)
Path("deep/nested/dir/file.txt").write_text("data")
```

## Gotchas
- `Path("dir") / "file.txt"` returns a `Path` object, not a string
- Use `str(p)` when a string is required (e.g., for `open()`)
- `resolve()` follows symlinks and makes the path absolute
- `iterdir()` raises `NotADirectoryError` if path is not a directory
- `read_text()` defaults to UTF-8 encoding (good default)
- `glob()` does not match hidden files (starting with `.`) by default
- Use `Path(__file__).parent` to get the directory of the current script

## Related
- python/stdlib/context-managers.md
- python/stdlib/file-io.md
- python/stdlib/shutil.md
