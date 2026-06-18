---
id: "anti-patterns-go-defer-in-loop"
title: "Go Anti-Pattern: defer Inside a Loop"
language: "go"
category: "anti-patterns"
tags: ["antipatterns", "go", "golang", "defer", "loop", "resource-leak", "memory"]
version: "n/a"
retrieval_hint: "Go defer inside loop resource leak file handle not closed memory deferred function stack LIFO closure scope"
last_verified: "2026-05-24"
confidence: "high"
---

# Go Anti-Pattern: defer Inside a Loop

## When to Use
- Reviewing Go code for resource leaks in loops
- Training LLMs to handle deferred cleanup correctly
- Processing files, database rows, or network connections in batch
- Understanding defer semantics in loop contexts

## Standard Pattern

```go
package main

import (
    "database/sql"
    "fmt"
    "os"
)

// ---------------------------------------------------------------------------
// WRONG: defer file.Close() inside a for loop
// ---------------------------------------------------------------------------

// WRONG: File handles accumulate until the function returns
func processFiles(files []string) {
    for _, file := range files {
        f, err := os.Open(file)
        if err != nil {
            log.Printf("Failed to open %s: %v", file, err)
            continue
        }
        defer f.Close() // ❌ Not closed until processFiles() returns!
        // If 1000 files are processed, 1000 file handles stay open
        process(f)
    }
    // All 1000 files are finally closed here — likely hitting fd limit
}

// CORRECT: Close explicitly — no defer in loop
func processFiles(files []string) {
    for _, file := range files {
        f, err := os.Open(file)
        if err != nil {
            log.Printf("Failed to open %s: %v", file, err)
            continue
        }
        process(f)
        f.Close() // ✅ Closed immediately
    }
}

// CORRECT: Wrap loop body in closure to use defer safely
func processFiles(files []string) {
    for _, file := range files {
        func() {
            f, err := os.Open(file)
            if err != nil {
                log.Printf("Failed to open %s: %v", file, err)
                return
            }
            defer f.Close() // ✅ Closed when anonymous function returns
            process(f)
        }()
    }
}

// ---------------------------------------------------------------------------
// WRONG: defer rows.Close() / stmt.Close() in database query loop
// ---------------------------------------------------------------------------

// WRONG: Database connections pile up
func processRecords(db *sql.DB) error {
    rows, err := db.Query("SELECT id, name FROM users")
    if err != nil {
        return err
    }
    defer rows.Close() // Good: close rows when function returns

    for rows.Next() {
        var id int
        var name string
        rows.Scan(&id, &name)

        // WRONG: defer in loop — prepared statement handle not released
        stmt, err := db.Prepare("UPDATE users SET name = ? WHERE id = ?")
        if err != nil {
            return err
        }
        defer stmt.Close() // ❌ Stays open until processRecords() returns
        stmt.Exec(name, id)
    }
    return rows.Err()
}

// CORRECT: Prepare statement OUTSIDE the loop
func processRecords(db *sql.DB) error {
    stmt, err := db.Prepare("UPDATE users SET name = ? WHERE id = ?")
    if err != nil {
        return err
    }
    defer stmt.Close() // ✅ Closed when function returns

    rows, err := db.Query("SELECT id, name FROM users")
    if err != nil {
        return err
    }
    defer rows.Close()

    for rows.Next() {
        var id int
        var name string
        rows.Scan(&id, &name)
        stmt.Exec(name, id)
    }
    return rows.Err()
}

// ---------------------------------------------------------------------------
// WRONG: defer mutex.Unlock() inside loop
// ---------------------------------------------------------------------------

// WRONG: Lock held until function exits — effectively a deadlock in loops
func updateAll(items []Item, mu *sync.Mutex) {
    for _, item := range items {
        mu.Lock()
        defer mu.Unlock() // ❌ Only unlocked when updateAll() returns!
        item.Process()
    }
    // Only the first item gets processed — then deadlock on the next iteration
}

// CORRECT: Lock/unlock within the loop
func updateAll(items []Item, mu *sync.Mutex) {
    for _, item := range items {
        mu.Lock()
        item.Process()
        mu.Unlock() // ✅ Released immediately
    }
}

// CORRECT: Use closure to scope defer
func updateAll(items []Item, mu *sync.Mutex) {
    for _, item := range items {
        func() {
            mu.Lock()
            defer mu.Unlock() // ✅ Released when anonymous function returns
            item.Process()
        }()
    }
}

// ---------------------------------------------------------------------------
// WRONG: defer time measurement in loop (LIFO ordering gotcha)
// ---------------------------------------------------------------------------

// WRONG: Defer is LIFO — timing is nested and wrong
func processAll(items []string) {
    for i, item := range items {
        defer fmt.Printf("Item %d done at %v\n", i, time.Now())
        // All prints happen at function exit, in reverse order
        // They all print the same (final) time
    }
}

// CORRECT: Use explicit timing
func processAll(items []string) {
    for i, item := range items {
        start := time.Now()
        process(item)
        fmt.Printf("Item %d took %v\n", i, time.Since(start))
    }
}

// ---------------------------------------------------------------------------
// WRONG: defer in infinite loop (never executes)
// ---------------------------------------------------------------------------

// WRONG: Infinite loop means defer never runs
func watchDirectory() {
    for {
        f, err := os.Open("/watched/dir")
        if err != nil {
            continue
        }
        defer f.Close() // ❌ Never reached — loop never breaks
        // File handle leaks every iteration
    }
}

// CORRECT: Close manually in infinite loop (no defer)
func watchDirectory() {
    for {
        f, err := os.Open("/watched/dir")
        if err != nil {
            time.Sleep(time.Second)
            continue
        }
        readDirectory(f)
        f.Close() // ✅ Closed before next iteration
    }
}
```

## Common Mistakes
The most common error is using `defer` to close file handles, database rows, or mutexes inside a loop — deferred calls don't execute until the **function returns**, not when the loop iteration ends. A loop processing 10,000 files with `defer f.Close()` holds 10,000 open file descriptors until the entire function completes, which typically hits the OS file descriptor limit (usually 256-1024). Second: deferring mutex unlocks inside a loop creates a deadlock on the second iteration.

## Gotchas
- `defer` inside a loop defers execution until the **enclosing function** returns — NOT when the loop iteration completes
- File descriptors are a limited OS resource (typically 256-1024 soft limit on Linux, 512 on macOS) — looping with deferred close guarantees exhaustion
- `Mutex.Lock()` / `defer Mutex.Unlock()` in a loop causes an immediate deadlock on the second iteration
- The closure wrapper `func() { ... }()` is the idiomatic Go pattern for scoped defer inside loops
- `defer` is LIFO (last-in-first-out) — all deferred calls in a loop fire in reverse order at function exit
- `db.Rows` / `sql.Stmt` are pooled resources — not closing them per-iteration leaks connections from the connection pool
- `defer recover()` in a loop's closure catches panics per-iteration instead of crashing the whole loop
- Panic inside a loop with `defer` doesn't trigger deferred calls from earlier iterations — they're evaluated but skipped by the panic
- Closing files inside the loop body (without defer) is cleaner but risks forgetting on error paths — always close both on success and error
- Go's `defer` evaluates its arguments immediately — if you defer `f.Close()`, it captures `f` at that moment, which is fine for files but matters for other patterns
- The closure pattern `func() { defer ... }()` allocates a new closure per iteration — negligible cost, but worth noting in tight loops

## Related
- anti-patterns/go-antipatterns.md
