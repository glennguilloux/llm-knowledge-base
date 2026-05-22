---
id: "python-data-pandas-basics"
title: "Pandas Common Operations"
language: "python"
category: "data"
tags: ["pandas", "dataframe", "csv", "data-processing", "analysis", "series", "groupby"]
version: "3.10+"
retrieval_hint: "pandas dataframe csv data processing analysis series groupby merge filter"
last_verified: "2026-05-22"
confidence: "high"
---

# Pandas Common Operations

## When to Use
- Reading, transforming, and analyzing tabular data (CSV, Excel, SQL)
- Data cleaning and preprocessing for ML pipelines
- Aggregation, grouping, and pivot operations
- Merging datasets from multiple sources

## Standard Pattern

```python
import pandas as pd
import numpy as np


# --- Reading data ---
def load_csv(path: str) -> pd.DataFrame:
    """Load CSV with common options."""
    return pd.read_csv(
        path,
        encoding="utf-8",
        parse_dates=["created_at"],  # Auto-parse date columns
        na_values=["", "NA", "N/A", "null"],  # Treat as NaN
    )


def load_excel(path: str, sheet: str = "Sheet1") -> pd.DataFrame:
    """Load Excel file."""
    return pd.read_excel(path, sheet_name=sheet)


# --- Filtering and selection ---
def filter_active_users(df: pd.DataFrame) -> pd.DataFrame:
    """Filter rows by condition."""
    return df[df["status"] == "active"]


def select_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Select specific columns."""
    return df[["name", "email", "created_at"]]


def filter_complex(df: pd.DataFrame) -> pd.DataFrame:
    """Complex filtering with multiple conditions."""
    mask = (df["age"] >= 18) & (df["status"] == "active") & (df["email"].notna())
    return df[mask]


# --- Adding and modifying columns ---
def add_computed_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add computed columns."""
    df = df.copy()  # Don't mutate original
    df["full_name"] = df["first_name"] + " " + df["last_name"]
    df["is_adult"] = df["age"] >= 18
    df["domain"] = df["email"].str.split("@").str[1]
    return df


# --- Aggregation ---
def summarize_by_group(df: pd.DataFrame) -> pd.DataFrame:
    """Group and aggregate."""
    return (
        df.groupby("department")
        .agg(
            count=("id", "count"),
            avg_salary=("salary", "mean"),
            max_salary=("salary", "max"),
        )
        .reset_index()
    )


# --- Merging datasets ---
def merge_user_orders(users: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    """Merge users with their orders."""
    return users.merge(orders, on="user_id", how="left")


# --- Handling missing values ---
def clean_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values."""
    df = df.copy()
    df["name"] = df["name"].fillna("Unknown")
    df["age"] = df["age"].fillna(df["age"].median())
    df = df.dropna(subset=["email"])  # Drop rows where email is missing
    return df


# --- Sorting ---
def sort_data(df: pd.DataFrame) -> pd.DataFrame:
    """Sort by multiple columns."""
    return df.sort_values(["department", "salary"], ascending=[True, False])


# --- Export ---
def export_results(df: pd.DataFrame, path: str) -> None:
    """Export to CSV."""
    df.to_csv(path, index=False, encoding="utf-8")
```

## Common Mistakes

```python
# WRONG: Modifying a slice (SettingWithCopyWarning)
df[df["age"] > 18]["status"] = "adult"  # May not work!

# CORRECT: Use .loc[] for assignment
df.loc[df["age"] > 18, "status"] = "adult"

# WRONG: Iterating over rows (extremely slow)
for index, row in df.iterrows():
    row["total"] = row["price"] * row["quantity"]  # 1000x slower than vectorized

# CORRECT: Vectorized operations
df["total"] = df["price"] * df["quantity"]

# WRONG: Not using copy() when modifying
filtered = df[df["age"] > 18]
filtered["status"] = "adult"  # May modify original df!

# CORRECT: Explicit copy
filtered = df[df["age"] > 18].copy()
filtered["status"] = "adult"

# WRONG: Using apply() when vectorized is possible
df["doubled"] = df["value"].apply(lambda x: x * 2)  # Slow

# CORRECT: Direct vectorized operation
df["doubled"] = df["value"] * 2

# WRONG: Ignoring dtypes (memory waste)
df = pd.read_csv("huge.csv")  # May use 10x more memory than needed

# CORRECT: Optimize dtypes
df = pd.read_csv("huge.csv", dtype={"id": "int32", "category": "category"})
```

## Gotchas
- `df[condition]` returns a view or copy depending on context — always use `.copy()` if you plan to modify
- `SettingWithCopyWarning` means you might be modifying a view, not the original — use `.loc[]`
- `iterrows()` is extremely slow — prefer vectorized operations, `apply()`, or `itertuples()`
- Pandas uses NaN for missing values; `None` in a numeric column becomes NaN
- `groupby()` doesn't include the group column in the result by default — use `as_index=False` or `reset_index()`
- `merge()` with `how="left"` keeps all rows from the left DataFrame, even if no match in right
- CSV reading infers types — use `dtype` parameter for consistent behavior

## Related
- python/stdlib/file-io.md
- python/data/pydantic-v2/models.md
