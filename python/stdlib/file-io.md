---
id: "python-stdlib-file-io"
title: "File I/O Patterns"
language: "python"
category: "stdlib"
tags: ["file-io", "open", "pathlib", "csv", "json", "tempfile", "encoding"]
version: "3.10+"
retrieval_hint: "file read write open pathlib csv json tempfile encoding"
last_verified: "2026-05-22"
confidence: "high"
---

# File I/O Patterns

## When to Use
- Reading and writing text or binary files
- Parsing CSV, JSON, or other structured file formats
- Working with temporary files and directories
- Handling file encoding (UTF-8, Latin-1, etc.)

## Standard Pattern

```python
from pathlib import Path
import csv
import json
import tempfile

# Reading text files (pathlib — preferred)
content = Path("data.txt").read_text(encoding="utf-8")

# Writing text files
Path("output.txt").write_text("Hello, world!", encoding="utf-8")

# Reading with context manager (for large files, line by line)
with open("large.log", encoding="utf-8") as f:
    for line in f:
        process(line.strip())

# Appending to a file
with open("log.txt", "a", encoding="utf-8") as f:
    f.write("New log entry\n")

# Reading binary files
data = Path("image.png").read_bytes()
Path("copy.png").write_bytes(data)

# CSV reading
with open("data.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row["name"], row["age"])

# CSV writing
with open("output.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "age"])
    writer.writeheader()
    writer.writerow({"name": "Alice", "age": 30})

# JSON reading/writing
data = json.loads(Path("config.json").read_text(encoding="utf-8"))
Path("output.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

# Temporary files
with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
    tmp.write("temporary data")
    tmp_path = tmp.name
# Use tmp_path, then clean up
Path(tmp_path).unlink(missing_ok=True)

# Temporary directory
with tempfile.TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir) / "data.txt"
    tmp_path.write_text("temp data")
    # Directory and contents auto-deleted on exit

# Globbing for files
for md_file in Path("src").rglob("*.md"):
    print(md_file.name)

# Checking file existence
p = Path("config.yaml")
if p.exists() and p.is_file():
    config = p.read_text()
```

## Common Mistakes

```python
# WRONG: Not specifying encoding
with open("data.txt") as f:  # Uses system default (may be Latin-1 on Windows)
    content = f.read()

# CORRECT: Always specify encoding
with open("data.txt", encoding="utf-8") as f:
    content = f.read()

# WRONG: Not using newline="" for CSV
with open("data.csv", "w") as f:
    writer = csv.writer(f)  # Extra blank lines on Windows

# CORRECT: Use newline="" for CSV files
with open("data.csv", "w", newline="") as f:
    writer = csv.writer(f)

# WRONG: Reading entire large file into memory
content = Path("huge.log").read_text()  # May cause OOM

# CORRECT: Process line by line
with open("huge.log", encoding="utf-8") as f:
    for line in f:
        process(line)

# WRONG: Not handling file not found
data = Path("config.json").read_text()  # FileNotFoundError

# CORRECT: Check existence or handle exception
p = Path("config.json")
if p.exists():
    data = p.read_text()
else:
    data = "{}"

# WRONG: Forgetting to close file on error
f = open("data.txt")
data = f.read()
process(data)  # If this raises, file is never closed
f.close()

# CORRECT: Use context manager
with open("data.txt", encoding="utf-8") as f:
    data = f.read()
process(data)  # File closed even if process() raises
```

## Gotchas
- Default encoding varies by OS — always specify `encoding="utf-8"` explicitly
- `csv.reader` and `csv.writer` need `newline=""` to avoid extra blank lines on Windows
- `Path.read_text()` loads entire file into memory — use `open()` with iteration for large files
- `tempfile.NamedTemporaryFile(delete=False)` requires manual cleanup
- `Path.write_text()` overwrites existing files without warning
- Binary mode (`"rb"`, `"wb"`) is required for non-text files — text mode corrupts binary data
- `json.dumps` returns a string, `json.dump` writes to a file object
- `csv.DictReader` uses the first row as headers — ensure your CSV has a header row

## Related
- python/stdlib/pathlib.md
- python/stdlib/regex.md
- python/stdlib/env-config.md
