---
id: "python-data-polars-basics"
title: "Polars DataFrame Basics"
language: "python"
category: "data"
subcategory: "dataframe"
tags: ["polars", "dataframe", "data", "csv", "parquet", "fast", "lazy"]
version: "3.10+"
retrieval_hint: "Polars DataFrame CSV Parquet lazy evaluation expressions data processing"
last_verified: "2026-05-22"
confidence: "high"
---

# Polars DataFrame Basics

## When to Use
- Processing large datasets (100MB+) faster than pandas
- Data pipelines that benefit from lazy evaluation and query optimization
- Working with Parquet, CSV, or Arrow files
- ETL jobs where memory efficiency matters (streaming, lazy execution)

## Standard Pattern

```python
import polars as pl


# --- Reading data ---
df = pl.read_csv("data.csv")
df = pl.read_parquet("data.parquet")
df = pl.read_json("data.json")


# --- Basic operations ---
result = (
    df
    .filter(pl.col("age") > 18)                    # Filter rows
    .select([                                        # Select columns
        pl.col("name"),
        pl.col("age"),
        (pl.col("salary") * 1.1).alias("adjusted"), # Computed column
    ])
    .sort("age", descending=True)                   # Sort
    .head(10)                                        # Limit
)


# --- Groupby and aggregation ---
summary = (
    df
    .group_by("department")
    .agg([
        pl.col("salary").mean().alias("avg_salary"),
        pl.col("salary").max().alias("max_salary"),
        pl.col("name").count().alias("headcount"),
    ])
    .sort("avg_salary", descending=True)
)


# --- Lazy evaluation (recommended for large data) ---
lazy_result = (
    pl.scan_csv("huge_file.csv")        # Doesn't load data yet
    .filter(pl.col("status") == "active")
    .select(["id", "name", "created_at"])
    .sort("created_at")
    .limit(100)
    .collect()                           # Executes optimized query
)


# --- Joins ---
orders = pl.read_csv("orders.csv")
customers = pl.read_csv("customers.csv")

joined = orders.join(customers, on="customer_id", how="left")


# --- Write output ---
result.write_csv("output.csv")
result.write_parquet("output.parquet")


# --- Add computed columns ---
enriched = df.with_columns([
    (pl.col("first") + " " + pl.col("last")).alias("full_name"),
    pl.col("date").str.strptime(pl.Date, "%Y-%m-%d").alias("parsed_date"),
    pl.when(pl.col("score") > 90).then(pl.lit("A"))
      .when(pl.col("score") > 80).then(pl.lit("B"))
      .otherwise(pl.lit("C")).alias("grade"),
])
```

## Common Mistakes

```python
# WRONG: Using eager mode for large files (loads everything into memory)
df = pl.read_csv("10gb_file.csv")  # OOM risk
result = df.filter(pl.col("x") > 5)

# CORRECT: Use lazy mode for large files
result = pl.scan_csv("10gb_file.csv").filter(pl.col("x") > 5).collect()

# WRONG: Using pandas-style column access
df["column_name"]  # Works but not idiomatic Polars

# CORRECT: Use expressions
df.select(pl.col("column_name"))

# WRONG: Chaining operations without collect (lazy frame not executed)
lazy = pl.scan_csv("data.csv").filter(pl.col("x") > 5)
print(lazy)  # Prints query plan, not data!

# CORRECT: Call .collect() to execute
result = lazy.collect()

# WRONG: Using Python loops instead of expressions
for row in df.iter_rows():  # Very slow
    if row[1] > 10:
        # process

# CORRECT: Use vectorized expressions
result = df.filter(pl.col("value") > 10)
```

## Gotchas
- Polars expressions are lazy — they build a query plan until `.collect()` is called
- `pl.scan_csv()` returns a `LazyFrame` (no data loaded); `pl.read_csv()` returns a `DataFrame`
- Column names use `pl.col("name")`, not string indexing like pandas
- Polars doesn't have an index — rows are accessed by position or filtered by column values
- `with_columns()` adds/replaces columns; `select()` returns only specified columns
- Polars is zero-copy with Arrow — operations don't duplicate memory unnecessarily
- Use `pl.concat()` for vertical stacking; `pl.join()` for horizontal merging
- String operations use `pl.col("x").str.method()` namespace

## Related
- python/data/pandas/basics.md
- python/stdlib/csv-module.md
- python/web/fastapi/sse-streaming.md
