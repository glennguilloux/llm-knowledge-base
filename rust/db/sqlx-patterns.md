---
id: "rust-db-sqlx-patterns"
title: "Rust SQLx Async Database Patterns"
language: "rust"
category: "db"
subcategory: "sql"
tags: ["rust", "sqlx", "async", "database", "postgresql", "query", "migrate"]
version: "1.75+"
retrieval_hint: "Rust SQLx async database PostgreSQL query compile-time migrate"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust SQLx Async Database Patterns

## When to Use
- Async database access in Rust (PostgreSQL, MySQL, SQLite)
- Compile-time query validation (SQL checked against real DB at build time)
- Type-safe queries with automatic result mapping
- Database migrations with sqlx-cli

## Standard Pattern

```rust
use sqlx::{PgPool, FromRow, query_as, query};
use serde::{Deserialize, Serialize};

// --- Model ---
#[derive(Debug, FromRow, Serialize, Deserialize)]
struct User {
    id: i64,
    name: String,
    email: String,
    created_at: chrono::NaiveDateTime,
}

// --- Setup ---
async fn create_pool(database_url: &str) -> Result<PgPool, sqlx::Error> {
    PgPool::connect(database_url).await
}

// --- CRUD ---
async fn create_user(pool: &PgPool, name: &str, email: &str) -> Result<User, sqlx::Error> {
    query_as::<_, User>(
        "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *"
    )
    .bind(name)
    .bind(email)
    .fetch_one(pool)
    .await
}

async fn get_user(pool: &PgPool, id: i64) -> Result<Option<User>, sqlx::Error> {
    query_as::<_, User>("SELECT * FROM users WHERE id = $1")
        .bind(id)
        .fetch_optional(pool)
        .await
}

async fn list_users(pool: &PgPool, limit: i64, offset: i64) -> Result<Vec<User>, sqlx::Error> {
    query_as::<_, User>("SELECT * FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2")
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
}

async fn update_user(pool: &PgPool, id: i64, name: &str) -> Result<User, sqlx::Error> {
    query_as::<_, User>("UPDATE users SET name = $1 WHERE id = $2 RETURNING *")
        .bind(name)
        .bind(id)
        .fetch_one(pool)
        .await
}

async fn delete_user(pool: &PgPool, id: i64) -> Result<bool, sqlx::Error> {
    let result = query("DELETE FROM users WHERE id = $1")
        .bind(id)
        .execute(pool)
        .await?;
    Ok(result.rows_affected() > 0)
}

// --- Transaction ---
async fn transfer(pool: &PgPool, from: i64, to: i64, amount: f64) -> Result<(), sqlx::Error> {
    let mut tx = pool.begin().await?;

    sqlx::query("UPDATE accounts SET balance = balance - $1 WHERE id = $2")
        .bind(amount)
        .bind(from)
        .execute(&mut *tx)
        .await?;

    sqlx::query("UPDATE accounts SET balance = balance + $1 WHERE id = $2")
        .bind(amount)
        .bind(to)
        .execute(&mut *tx)
        .await?;

    tx.commit().await
}

// --- Compile-time checked queries (requires DATABASE_URL at build time) ---
async fn get_user_checked(pool: &PgPool, id: i64) -> Result<Option<User>, sqlx::Error> {
    sqlx::query_as!(User, "SELECT * FROM users WHERE id = $1", id)
        .fetch_optional(pool)
        .await
}
```

## Common Mistakes

```rust
// WRONG: Not handling sqlx::Error::RowNotFound
let user: User = query_as("SELECT * FROM users WHERE id = $1")
    .bind(id)
    .fetch_one(pool)
    .await?;  // Panics if not found!

// CORRECT: Use fetch_optional for "maybe not found"
let user: Option<User> = query_as("SELECT * FROM users WHERE id = $1")
    .bind(id)
    .fetch_optional(pool)
    .await?;

// WRONG: String formatting for SQL (injection!)
let query = format!("SELECT * FROM users WHERE name = '{name}'");
sqlx::query(&query).fetch_all(pool).await?;

// CORRECT: Use parameterized queries
query_as::<_, User>("SELECT * FROM users WHERE name = $1")
    .bind(name)
    .fetch_all(pool)
    .await?;

// WRONG: Not using connection pool
let conn = PgPool::connect(url).await?;  // New connection per request!

// CORRECT: Share the pool
let pool = PgPool::connect(url).await?;
// Pass pool to handlers

// WRONG: Forgetting to commit transaction
let mut tx = pool.begin().await?;
// ... operations ...
// tx.commit().await?;  // Transaction rolled back!

// CORRECT: Always commit (or let it auto-rollback on drop)
tx.commit().await?;
```

## Gotchas
- `query_as!` macro checks SQL at compile time — requires `DATABASE_URL` env var
- `fetch_one` returns `RowNotFound` error if no rows; `fetch_optional` returns `None`
- `fetch_all` returns `Vec<T>` — empty vec if no rows
- Transactions auto-rollback on drop if not committed
- `PgPool::connect()` doesn't verify connection — use `pool.acquire()` to test
- Use `sqlx::migrate!()` macro to run migrations at startup
- `FromRow` derive maps column names to struct fields by default
- Bind order matters — `$1, $2, $3` must match `.bind()` call order

## Real-World Example

### Repository Pattern with SQLx: CRUD + Transactions + Error Mapping

```rust
use sqlx::{PgPool, Row, postgres::PgRow};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum RepoError {
    #[error("not found: {0}")]
    NotFound(String),
    #[error("database error: {0}")]
    Database(#[from] sqlx::Error),
}

pub struct UserRepo {
    pool: PgPool,
}

#[derive(Debug, sqlx::FromRow)]
pub struct User {
    pub id: i64,
    pub email: String,
    pub name: String,
}

impl UserRepo {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    pub async fn find_by_id(&self, id: i64) -> Result<User, RepoError> {
        let user = sqlx::query_as::<_, User>(
            "SELECT id, email, name FROM users WHERE id = $1",
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?
        .ok_or(RepoError::NotFound(format!("user {}", id)))?;
        Ok(user)
    }

    pub async fn create(&self, email: &str, name: &str) -> Result<User, RepoError> {
        let user = sqlx::query_as::<_, User>(
            "INSERT INTO users (email, name) VALUES ($1, $2) RETURNING id, email, name",
        )
        .bind(email)
        .bind(name)
        .fetch_one(&self.pool)
        .await?;
        Ok(user)
    }

    pub async fn transfer_credits(
        &self,
        from_id: i64,
        to_id: i64,
        amount: i64,
    ) -> Result<(), RepoError> {
        let mut tx = self.pool.begin().await?;
        sqlx::query("UPDATE users SET credits = credits - $1 WHERE id = $2")
            .bind(amount)
            .bind(from_id)
            .execute(&mut *tx)
            .await?;
        sqlx::query("UPDATE users SET credits = credits + $1 WHERE id = $2")
            .bind(amount)
            .bind(to_id)
            .execute(&mut *tx)
            .await?;
        tx.commit().await?;
        Ok(())
    }
}
```

## Related
- rust/web/axum-deep.md
- rust/stdlib/error-crates.md
