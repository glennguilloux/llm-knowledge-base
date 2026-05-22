---
id: "go-db-database-sql"
title: "Go database/sql and sqlx Patterns"
language: "go"
category: "db"
subcategory: "sql"
tags: ["go", "database", "sql", "sqlx", "postgresql", "connection-pool"]
version: "1.21+"
retrieval_hint: "Go database sql sqlx PostgreSQL connection pool query row scan"
last_verified: "2026-05-22"
confidence: "high"
---

# Go database/sql and sqlx Patterns

## When to Use
- Database access in Go applications (PostgreSQL, MySQL, SQLite)
- Type-safe query results with struct scanning
- Connection pooling and lifecycle management
- Raw SQL queries without an ORM

## Standard Pattern

```go
package main

import (
    "context"
    "database/sql"
    "fmt"
    "log"
    "time"

    _ "github.com/lib/pq"  // PostgreSQL driver
    "github.com/jmoiron/sqlx"
)

// --- Connection setup ---
func initDB(dsn string) (*sqlx.DB, error) {
    db, err := sqlx.Connect("postgres", dsn)
    if err != nil {
        return nil, fmt.Errorf("connect: %w", err)
    }

    db.SetMaxOpenConns(25)
    db.SetMaxIdleConns(10)
    db.SetConnMaxLifetime(5 * time.Minute)
    db.SetConnMaxIdleTime(1 * time.Minute)

    if err := db.PingContext(context.Background()); err != nil {
        return nil, fmt.Errorf("ping: %w", err)
    }
    return db, nil
}

// --- Model ---
type User struct {
    ID        int64     `db:"id"`
    Name      string    `db:"name"`
    Email     string    `db:"email"`
    CreatedAt time.Time `db:"created_at"`
}

// --- CRUD with sqlx ---
type UserRepo struct {
    db *sqlx.DB
}

func (r *UserRepo) Create(ctx context.Context, name, email string) (*User, error) {
    var user User
    err := r.db.QueryRowxContext(ctx,
        "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *",
        name, email,
    ).StructScan(&user)
    if err != nil {
        return nil, fmt.Errorf("create user: %w", err)
    }
    return &user, nil
}

func (r *UserRepo) GetByID(ctx context.Context, id int64) (*User, error) {
    var user User
    err := r.db.GetContext(ctx, &user,
        "SELECT * FROM users WHERE id = $1", id,
    )
    if err == sql.ErrNoRows {
        return nil, nil
    }
    if err != nil {
        return nil, fmt.Errorf("get user %d: %w", id, err)
    }
    return &user, nil
}

func (r *UserRepo) List(ctx context.Context, limit, offset int) ([]User, error) {
    var users []User
    err := r.db.SelectContext(ctx, &users,
        "SELECT * FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2",
        limit, offset,
    )
    if err != nil {
        return nil, fmt.Errorf("list users: %w", err)
    }
    return users, nil
}

func (r *UserRepo) Update(ctx context.Context, id int64, name, email string) error {
    result, err := r.db.ExecContext(ctx,
        "UPDATE users SET name = $1, email = $2 WHERE id = $3",
        name, email, id,
    )
    if err != nil {
        return fmt.Errorf("update user: %w", err)
    }
    rows, _ := result.RowsAffected()
    if rows == 0 {
        return fmt.Errorf("user %d not found", id)
    }
    return nil
}

// --- Transaction ---
func (r *UserRepo) Transfer(ctx context.Context, fromID, toID int64, amount float64) error {
    tx, err := r.db.BeginTxx(ctx, nil)
    if err != nil {
        return fmt.Errorf("begin tx: %w", err)
    }
    defer tx.Rollback()  // No-op if committed

    _, err = tx.ExecContext(ctx,
        "UPDATE accounts SET balance = balance - $1 WHERE id = $2", amount, fromID,
    )
    if err != nil {
        return fmt.Errorf("debit: %w", err)
    }

    _, err = tx.ExecContext(ctx,
        "UPDATE accounts SET balance = balance + $1 WHERE id = $2", amount, toID,
    )
    if err != nil {
        return fmt.Errorf("credit: %w", err)
    }

    return tx.Commit()
}
```

## Common Mistakes

```go
// WRONG: Not closing rows (connection leak)
rows, _ := db.QueryContext(ctx, "SELECT * FROM users")
for rows.Next() {
    // process
}
// rows.Close() never called!

// CORRECT: defer rows.Close()
rows, err := db.QueryContext(ctx, "SELECT * FROM users")
if err != nil {
    return err
}
defer rows.Close()

// WRONG: Ignoring sql.ErrNoRows
var user User
err := db.GetContext(ctx, &user, "SELECT * FROM users WHERE id = $1", id)
if err != nil {
    return err  // Returns error for "not found" too
}

// CORRECT: Handle ErrNoRows separately
err := db.GetContext(ctx, &user, "SELECT * FROM users WHERE id = $1", id)
if err == sql.ErrNoRows {
    return nil, nil  // Not found
}

// WRONG: Using fmt.Sprintf for queries (SQL injection!)
query := fmt.Sprintf("SELECT * FROM users WHERE name = '%s'", name)

// CORRECT: Use parameterized queries
db.QueryContext(ctx, "SELECT * FROM users WHERE name = $1", name)

// WRONG: Creating new connections per request
func handler(w http.ResponseWriter, r *http.Request) {
    db, _ := sql.Open("postgres", dsn)  // New pool per request!
}

// CORRECT: Share the connection pool
var db *sqlx.DB  // Global or dependency-injected
```

## Gotchas
- `sql.Open()` doesn't connect — use `sqlx.Connect()` or `db.Ping()` to verify
- `db.GetContext()` expects exactly one row — returns `ErrNoRows` if none
- `db.SelectContext()` returns multiple rows into a slice
- `QueryRowxContext().StructScan()` for single-row queries returning structs
- Always `defer rows.Close()` after `db.QueryContext()` — connection leak otherwise
- Transactions: `defer tx.Rollback()` is safe — Rollback is a no-op after Commit
- Use `$1, $2, $3` for PostgreSQL; `?` for MySQL/SQLite
- `sql.ErrNoRows` is not an application error — handle it explicitly

## Related
- go/web/http-server.md
- go/testing/testing.md
- go/stdlib/error-handling.md
