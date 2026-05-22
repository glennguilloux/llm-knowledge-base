---
id: "python-db-alembic-advanced"
title: "Alembic Downgrade Strategies and Data Migrations"
language: "python"
category: "db"
subcategory: "migrations"
tags: ["alembic", "migration", "downgrade", "data", "schema", "branching"]
version: "3.10+"
retrieval_hint: "Alembic downgrade data migration branching merge schema migration"
last_verified: "2026-05-22"
confidence: "high"
---

# Alembic Downgrade Strategies and Data Migrations

## When to Use
- Reverting a bad migration in production (downgrade)
- Migrating data alongside schema changes (rename column, transform values)
- Managing multiple developers creating conflicting migrations (branching)
- Complex schema changes that need careful ordering (add column → backfill → add constraint)

## Standard Pattern

```python
"""Example migration: add column with backfill and downgrade support.

Revision ID: abc123
Revises: def456
"""

from alembic import op
import sqlalchemy as sa

revision = "abc123"
down_revision = "def456"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Add column as nullable
    op.add_column("users", sa.Column("full_name", sa.String(200), nullable=True))

    # Step 2: Backfill data from existing columns
    op.execute("UPDATE users SET full_name = first_name || ' ' || last_name")

    # Step 3: Make NOT NULL (only after backfill)
    op.alter_column("users", "full_name", nullable=False)

    # Step 4: Drop old columns
    op.drop_column("users", "first_name")
    op.drop_column("users", "last_name")


def downgrade() -> None:
    # Reverse in opposite order
    op.add_column("users", sa.Column("first_name", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(100), nullable=True))

    # Reverse backfill
    op.execute("""
        UPDATE users
        SET first_name = split_part(full_name, ' ', 1),
            last_name = split_part(full_name, ' ', 2)
    """)

    op.alter_column("users", "first_name", nullable=False)
    op.alter_column("users", "last_name", nullable=False)
    op.drop_column("users", "full_name")
```

```python
"""Data migration: transform JSON field to normalized table."""

from alembic import op
import sqlalchemy as sa
import json

revision = "data_001"
down_revision = "schema_002"


def upgrade() -> None:
    # Create target table
    op.create_table(
        "user_addresses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("street", sa.String(200)),
        sa.Column("city", sa.String(100)),
        sa.Column("zip_code", sa.String(20)),
    )

    # Migrate data using raw connection
    conn = op.get_bind()
    users = conn.execute(sa.text("SELECT id, address_json FROM users WHERE address_json IS NOT NULL"))
    for user in users:
        addr = json.loads(user.address_json)
        conn.execute(
            sa.text("INSERT INTO user_addresses (user_id, street, city, zip_code) VALUES (:uid, :s, :c, :z)"),
            {"uid": user.id, "s": addr["street"], "c": addr["city"], "z": addr["zip"]},
        )


def downgrade() -> None:
    op.drop_table("user_addresses")
```

```python
"""Merge migration for branching."""

revision = "merge_001"
down_revision = ("branch_a", "branch_b")  # Tuple = merge point
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op — just marks that both branches are merged
    pass


def downgrade() -> None:
    pass
```

## Common Mistakes

```python
# WRONG: No downgrade function (can't revert)
def upgrade() -> None:
    op.add_column("users", sa.Column("age", sa.Integer))

def downgrade() -> None:
    pass  # Can't revert!

# CORRECT: Always implement downgrade
def downgrade() -> None:
    op.drop_column("users", "age")

# WRONG: Adding NOT NULL column without default to existing table
op.add_column("users", sa.Column("role", sa.String(50), nullable=False))
# Fails if table has existing rows!

# CORRECT: Add nullable first, backfill, then constrain
op.add_column("users", sa.Column("role", sa.String(50), nullable=True))
op.execute("UPDATE users SET role = 'user'")
op.alter_column("users", "role", nullable=False)

# WRONG: Using ORM models in migrations
from app.models import User  # Model may change after migration was written!

# CORRECT: Use op.create_table or sa.text for raw SQL in migrations
op.create_table("users", sa.Column("id", sa.Integer, primary_key=True))

# WRONG: Not testing downgrade
# Always test: alembic downgrade -1 && alembic upgrade head
```

## Gotchas
- `op.get_bind()` returns the current connection — use it for data migrations
- Downgrades must be written at migration creation time — you can't auto-generate them for data migrations
- `sa.text()` is required for raw SQL in Alembic (not plain strings in newer versions)
- Branching: use `alembic merge -m "description" branch1 branch2` to create merge migrations
- `alembic downgrade -1` reverts one migration; `alembic downgrade base` reverts all
- Always test the full upgrade → downgrade → upgrade cycle before deploying
- Use `alembic stamp head` to mark existing databases as current without running migrations
- `op.batch_alter_table()` is required for SQLite (doesn't support ALTER TABLE well)

## Related
- python/db/sqlalchemy-2.0/models.md
- python/db/sqlalchemy-2.0/queries.md
- python/web/fastapi/dependency-injection.md
