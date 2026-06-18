---
id: "anti-patterns-go-recover-misuse"
title: "Go Anti-Pattern: recover Misuse"
language: "go"
category: "anti-patterns"
tags: ["antipatterns", "go", "golang", "recover", "panic", "error-handling", "defer"]
version: "n/a"
retrieval_hint: "Go recover panic inside goroutine deferred function defer panic not in same goroutine recover returns nil misuse net/http"
last_verified: "2026-05-24"
confidence: "high"
---

# Go Anti-Pattern: recover Misuse

## When to Use
- Reviewing Go code for panic recovery patterns
- Training LLMs to use recover correctly in production services
- Implementing middleware-level panic recovery in HTTP/gRPC servers
- Distinguishing between error handling and panic recovery

## Standard Pattern

```go
package main

import (
    "fmt"
    "log"
    "net/http"
    "runtime/debug"
)

// ---------------------------------------------------------------------------
// WRONG: recover() outside defer — always returns nil
// ---------------------------------------------------------------------------

// WRONG: recover called directly — cannot catch panics
func dangerousFunction() {
    recover() // ❌ Outside defer — always returns nil
    panic("something went wrong")
}

func main() {
    dangerousFunction() // PANIC — recover() did nothing!
    fmt.Println("Never reaches here")
}

// CORRECT: recover must be called directly inside a deferred function
func dangerousFunction() {
    defer func() {
        if r := recover(); r != nil {
            fmt.Println("Recovered from:", r)
        }
    }()
    panic("something went wrong")
}

// ---------------------------------------------------------------------------
// WRONG: recover() in a different goroutine
// ---------------------------------------------------------------------------

// WRONG: recover in goroutine A cannot catch panics from goroutine B
func main() {
    defer func() {
        if r := recover(); r != nil {
            fmt.Println("Recovered:", r) // ❌ Never catches panics from other goroutines
        }
    }()

    go func() {
        panic("goroutine B panicked") // PANIC — crashes the program!
    }()

    time.Sleep(time.Second)
    // Output: panic: goroutine B panicked
}

// CORRECT: recover in each goroutine individually
func main() {
    go func() {
        defer func() {
            if r := recover(); r != nil {
                log.Printf("Goroutine recovered: %v", r)
            }
        }()
        panic("goroutine B panicked") // ✅ Caught by this goroutine's recover
    }()

    time.Sleep(time.Second)
    fmt.Println("Program continues")
}

// ---------------------------------------------------------------------------
// WRONG: recover everything silently (hiding bugs)
// ---------------------------------------------------------------------------

// WRONG: Silent recover — bugs are hidden, not fixed
func processUserRequest(w http.ResponseWriter, r *http.Request) {
    defer func() {
        recover() // ❌ Silently discards panic info
    }()

    // If this panics due to a nil pointer, we never know
    user := findUser(r.Context(), r.URL.Query().Get("id"))
    fmt.Fprintf(w, "User: %s", user.Name)
}

// CORRECT: Log the panic and return a 500
func processUserRequest(w http.ResponseWriter, r *http.Request) {
    defer func() {
        if r := recover(); r != nil {
            log.Printf("PANIC in user request: %v\nStack: %s", r, debug.Stack())
            http.Error(w, "Internal Server Error", http.StatusInternalServerError)
        }
    }()

    user := findUser(r.Context(), r.URL.Query().Get("id"))
    fmt.Fprintf(w, "User: %s", user.Name)
}

// ---------------------------------------------------------------------------
// WRONG: Using panic/recover as try/catch (Go anti-pattern)
// ---------------------------------------------------------------------------

// WRONG: panic/recover as exception handling
func divideNumbers(a, b int) (result int) {
    defer func() {
        if r := recover(); r != nil {
            result = 0
        }
    }()

    if b == 0 {
        panic("division by zero") // ❌ panic for control flow!
    }
    return a / b
}

// CORRECT: Return error instead
func divideNumbers(a, b int) (int, error) {
    if b == 0 {
        return 0, fmt.Errorf("division by zero")
    }
    return a / b, nil
}

// ---------------------------------------------------------------------------
// WRONG: Recovering and continuing without re-panicking for unexpected panics
// ---------------------------------------------------------------------------

// WRONG: Recovering from nil pointer dereference and pretending nothing happened
func processItems(items []string) {
    defer func() {
        if r := recover(); r != nil {
            log.Printf("Recovered: %v", r)
            // ❌ Should re-panic — this is a programming bug, not a runtime condition
        }
    }()

    // nil pointer dereference — a programming bug
    var p *int
    *p = 42 // PANIC
}

// CORRECT: Re-panic unexpected panics after logging
func processItems(items []string) {
    defer func() {
        if r := recover(); r != nil {
            log.Printf("UNEXPECTED PANIC: %v\nStack: %s", r, debug.Stack())
            panic(r) // ✅ Re-panic — this is a bug that should crash and be fixed
        }
    }()

    var p *int
    *p = 42 // PANIC → logged → re-panics
}

// ---------------------------------------------------------------------------
// CORRECT: Using recover in HTTP middleware (the idiomatic pattern)
// ---------------------------------------------------------------------------

// CORRECT: Panic recovery middleware
func recoveryMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if r := recover(); r != nil {
                log.Printf("Recovered from panic in %s %s: %v",
                    r.Method, r.URL.Path, r)
                http.Error(w, "Internal Server Error", http.StatusInternalServerError)
            }
        }()
        next.ServeHTTP(w, r)
    })
}

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("/api/", apiHandler)

    // Wrap with recovery middleware
    server := recoveryMiddleware(mux)
    log.Fatal(http.ListenAndServe(":8080", server))
}

// ---------------------------------------------------------------------------
// WRONG: defer os.Exit() after recover (won't run)
// ---------------------------------------------------------------------------

// WRONG: os.Exit skips deferred functions
func main() {
    defer func() {
        if r := recover(); r != nil {
            log.Printf("Recovered: %v", r)
        }
        fmt.Println("Cleanup...") // ✅ This runs normally
    }()

    defer func() {
        // ❌ os.Exit() NEVER runs deferred functions
        // Even if called inside a defer, os.Exit bypasses all remaining defers
    }()

    panic("something went wrong")
    // The os.Exit pattern should just be the deferred cleanup above
}
```

## Common Mistakes
The biggest misuse is calling `recover()` outside of a deferred function — it always returns `nil` and does nothing, giving the false impression of safety. Second: using `panic/recover` as a try/catch substitute for normal error handling — Go's philosophy is to return errors, not throw exceptions. Third: silent recovery — catching a panic without logging it hides programming bugs. Fourth: forgetting that `recover()` in one goroutine cannot catch panics from another goroutine — each goroutine needs its own deferred recover.

## Gotchas
- `recover()` only works when called **directly** inside a deferred function — calling it indirectly (through another function) returns `nil`
- `recover()` in a defer captures the panic from the **same goroutine only** — panics in other goroutines crash the program regardless
- `net/http`'s default `ServeMux` does NOT recover panics — you MUST write your own recovery middleware or use a framework
- `recover()` returns the panic value as `any` — you can type-assert it: `if err, ok := r.(error); ok { ... }`
- `runtime/debug.Stack()` returns the stack trace of the **current goroutine** — very useful in recovery handlers
- `database/sql` Rows closure panics can be caught by recover in the right scope — but it's better to check `rows.Err()` and `rows.Close()`
- Silent `recover()` (calling it without using the return value) hides ALL panics — don't do this
- `recover()` DOES catch panics from `nil` pointer dereferences, index out of range, and assertion failures — but these are bugs, not runtime conditions
- Re-panicking (`panic(r)`) is the correct response for unexpected panics — you log them for debugging but still crash
- `os.Exit()` skips all deferred functions — if you call `os.Exit()` in a deferred recover block, your cleanup NEVER runs
- `log.Fatal()` calls `os.Exit()` internally — using it in a deferred panic handler also skips remaining defers
- `debug.PrintStack()` prints the stack trace to stderr — useful in recover for debugging without re-panicking
- The `recover()` built-in is only ~30 lines of Go runtime code — it's not magic, just a goroutine-local flag

## Related
- anti-patterns/go-antipatterns.md
