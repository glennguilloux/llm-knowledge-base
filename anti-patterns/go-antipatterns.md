---
id: "anti-patterns-go"
title: "Go Anti-Patterns"
language: "go"
category: "anti-patterns"
subcategory: "go"
tags: ["go", "anti-pattern", "goroutine-leak", "error-ignoring", "interface"]
version: "1.21+"
retrieval_hint: "Go anti-pattern goroutine leak error ignoring interface pollution naked return"
last_verified: "2026-05-22"
confidence: "high"
---

# Go Anti-Patterns

## When to Use
- Code review: identifying common Go mistakes
- Refactoring legacy Go code
- Onboarding new Go developers
- Preventing production issues

## Standard Pattern

See Common Mistakes below for WRONG/CORRECT code pairs.

## Common Mistakes

```go
// WRONG: Ignoring errors
data, _ := os.ReadFile("config.yaml")  // Error silently ignored
db.Exec("INSERT INTO users ...")       // Error silently ignored

// CORRECT: Always handle errors
data, err := os.ReadFile("config.yaml")
if err != nil {
    return fmt.Errorf("read config: %w", err)
}
if _, err := db.Exec("INSERT INTO users ..."); err != nil {
    return fmt.Errorf("insert user: %w", err)
}

// WRONG: Goroutine leaks
func fetchData(urls []string) []Result {
    results := make([]Result, len(urls))
    for i, url := range urls {
        go func(i int, url string) {
            results[i] = fetch(url)  // No synchronization!
        }(i, url)
    }
    return results  // Returns before goroutines complete
}

// CORRECT: Use WaitGroup and context
func fetchData(ctx context.Context, urls []string) ([]Result, error) {
    results := make([]Result, len(urls))
    g, ctx := errgroup.WithContext(ctx)
    for i, url := range urls {
        i, url := i, url
        g.Go(func() error {
            result, err := fetchWithContext(ctx, url)
            if err != nil {
                return fmt.Errorf("fetch %s: %w", url, err)
            }
            results[i] = result
            return nil
        })
    }
    return results, g.Wait()
}

// WRONG: Interface pollution (too many interfaces)
type UserReader interface { GetByID(id int64) (*User, error) }
type UserWriter interface { Create(user *User) error }
type UserUpdater interface { Update(user *User) error }
type UserDeleter interface { Delete(id int64) error }
type UserRepository interface {
    UserReader; UserWriter; UserUpdater; UserDeleter
}

// CORRECT: Define interfaces where they're consumed, not where they're implemented
type UserFinder interface {
    FindByID(ctx context.Context, id int64) (*User, error)
}

// Service defines what it needs
type OrderService struct {
    users UserFinder  // Small, focused interface
}

// WRONG: Naked returns in long functions
func process(data []byte) (result []byte, err error) {
    // ... 50 lines of code ...
    // return  // What are we returning? Hard to follow!
}

// CORRECT: Explicit returns
func process(data []byte) ([]byte, error) {
    // ... code ...
    return result, nil
}

// WRONG: Loop variable capture in goroutines
for _, url := range urls {
    go func() {
        fetch(url)  // All goroutines use last value of url!
    }()
}

// CORRECT: Pass as parameter
for _, url := range urls {
    go func(u string) {
        fetch(u)
    }(url)
}

// WRONG: Using panic for error handling
func divide(a, b float64) float64 {
    if b == 0 {
        panic("division by zero")  // Crashes the program!
    }
    return a / b
}

// CORRECT: Return error
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, fmt.Errorf("division by zero")
    }
    return a / b, nil
}
```

## Gotchas
- Ignoring errors with `_` is acceptable only when you've documented why
- Goroutine leaks: always ensure goroutines can exit (context cancellation, channels)
- Don't create interfaces preemptively — let them emerge from actual usage
- Naked returns are acceptable only in very short functions (< 5 lines)
- Loop variable capture in goroutines is fixed in Go 1.22+ (per-iteration scope)
- `panic` is for truly unrecoverable errors — use `error` for everything else
- Don't over-abstract — Go favors simplicity over cleverness
- `defer` in loops accumulates — use anonymous functions to scope defers

## Related
- go/stdlib/error-handling.md
- go/stdlib/goroutines.md
- go/concurrency/sync-patterns.md
