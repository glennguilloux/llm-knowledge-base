---
id: "python-stdlib-csv-module"
title: "CSV Reading and Writing with the csv Module"
language: "python"
category: "stdlib"
subcategory: "file-formats"
tags: ["csv", "read", "write", "dictreader", "dictwriter", "pandas"]
version: "3.10+"
retrieval_hint: "CSV read write DictReader DictWriter pandas import export"
last_verified: "2026-05-22"
confidence: "high"
---

# CSV Reading and Writing with the csv Module

## When to Use
- Importing/exporting data from databases, spreadsheets, or APIs
- Processing data files from external systems (reports, logs, user uploads)
- Generating CSV reports or data feeds
- Lightweight data processing where pandas is overkill

## Standard Pattern

```python
import csv
from pathlib import Path
from typing import TextIO


# --- Reading CSV ---
def read_csv_basic(path: str) -> list[list[str]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header
        return [row for row in reader]


def read_csv_as_dicts(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


# --- Writing CSV ---
def write_csv_basic(path: str, rows: list[list[str]], header: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def write_csv_dicts(path: str, rows: list[dict], fieldnames: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# --- Streaming large CSV ---
def stream_large_csv(path: str, batch_size: int = 1000):
    """Yield batches of rows for memory-efficient processing."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        batch = []
        for row in reader:
            batch.append(row)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch


# --- Custom dialect ---
csv.register_dialect("pipe", delimiter="|", quoting=csv.QUOTE_MINIMAL)

with open("data.psv", newline="") as f:
    reader = csv.reader(f, dialect="pipe")
    for row in reader:
        print(row)


# --- TSV (tab-separated) ---
def read_tsv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return [row for row in reader]
```

## Common Mistakes

```python
# WRONG: Not using newline="" (extra blank lines on Windows)
with open("data.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["a", "b"])  # Extra blank line between rows on Windows

# CORRECT: Always use newline="" for CSV files
with open("data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["a", "b"])

# WRONG: Reading CSV with wrong encoding
with open("data.csv") as f:  # Uses system default encoding
    reader = csv.reader(f)  # Fails on non-ASCII characters

# CORRECT: Specify encoding explicitly
with open("data.csv", encoding="utf-8-sig") as f:  # utf-8-sig handles BOM
    reader = csv.reader(f)

# WRONG: Writing dict rows without fieldnames
writer = csv.DictWriter(f)  # Missing fieldnames!
writer.writerow({"name": "Alice", "age": 30})

# CORRECT: Always provide fieldnames
writer = csv.DictWriter(f, fieldnames=["name", "age"])
writer.writeheader()
writer.writerow({"name": "Alice", "age": 30})

# WRONG: Loading entire large CSV into memory
rows = list(csv.DictReader(open("huge.csv")))  # OOM risk

# CORRECT: Process in batches or iterate
for batch in stream_large_csv("huge.csv", batch_size=1000):
    process_batch(batch)
```

## Gotchas
- `newline=""` is mandatory for CSV files — without it, you get extra blank lines on Windows
- `csv.reader` returns strings for all values — convert types manually (`int(row["age"])`)
- `csv.DictReader` uses the first row as keys — if the header has duplicates, later values overwrite
- Use `encoding="utf-8-sig"` to handle BOM (Byte Order Mark) from Excel exports
- `csv.writer` doesn't handle nested data — flatten structures before writing
- `QUOTE_MINIMAL` (default) only quotes fields containing the delimiter; `QUOTE_ALL` quotes everything
- `csv.Sniffer` can auto-detect delimiter and quoting style from a sample
- For large files, pandas `read_csv()` with `chunksize` is often more convenient than the csv module

## Related
- python/stdlib/json-nested.md
- python/stdlib/file-io.md
- python/data/polars/basics.md
