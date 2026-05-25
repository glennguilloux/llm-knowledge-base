---
id: "go-concurrency-sync-patterns"
title: "Go sync Package: WaitGroup, Mutex, errgroup"
language: "go"
category: "concurrency"
subcategory: "sync"
tags: ["go", "sync", "waitgroup", "mutex", "errgroup", "once", "pool"]
version: "1.21+"
retrieval_hint: "Go sync WaitGroup Mutex errgroup Once Pool concurrent goroutine"
last_verified: "2026-05-24"
confidence: "high"
---

# Go sync Package: WaitGroup, Mutex, errgroup

## When to Use
- Coordinating multiple goroutines (WaitGroup)
- Protecting shared state from concurrent access (Mutex)
- Collecting errors from parallel goroutines (errgroup)
- One-time initialization (Once)

## Standard Pattern

```go
package main

import (
    "context"
    "fmt"
    "sync"

    "golang.org/x/sync/errgroup"
)

// --- WaitGroup: wait for all goroutines to finish ---
func fetchAll(urls []string) []Result {
    results := make([]Result, len(urls))
    var wg sync.WaitGroup

    for i, url := range urls {
        wg.Add(1)
        go func(i int, url string) {
            defer wg.Done()
            results[i] = fetch(url)
        }(i, url)
    }

    wg.Wait()
    return results
}

// --- Mutex: protect shared state ---
type SafeCounter struct {
    mu    sync.Mutex
    count int
}

func (c *SafeCounter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.count++
}

func (c *SafeCounter) Value() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.count
}

// --- errgroup: goroutines with error handling ---
func fetchAllWithErrors(ctx context.Context, urls []string) ([]Result, error) {
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

    if err := g.Wait(); err != nil {
        return nil, err
    }
    return results, nil
}

// --- errgroup with concurrency limit ---
func fetchLimited(ctx context.Context, urls []string, maxConcurrent int) ([]Result, error) {
    results := make([]Result, len(urls))

    g, ctx := errgroup.WithContext(ctx)
    g.SetLimit(maxConcurrent)

    for i, url := range urls {
        i, url := i, url
        g.Go(func() error {
            result, err := fetchWithContext(ctx, url)
            results[i] = result
            return err
        })
    }

    return results, g.Wait()
}

// --- Once: one-time initialization ---
var (
    instance *Database
    once     sync.Once
)

func GetDB() *Database {
    once.Do(func() {
        instance = connectDB()
    })
    return instance
}

// --- RWMutex: multiple readers, single writer ---
type Cache struct {
    mu   sync.RWMutex
    data map[string]string
}

func (c *Cache) Get(key string) (string, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    val, ok := c.data[key]
    return val, ok
}

func (c *Cache) Set(key, value string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.data[key] = value
}
```

## Common Mistakes

```go
// WRONG: goroutine with loop variable capture
for _, url := range urls {
    go func() {
        fetch(url)  // url is captured by reference — last value used!
    }()
}

// CORRECT: Pass as parameter
for _, url := range urls {
    go func(u string) {
        fetch(u)
    }(url)
}

// WRONG: WaitGroup Add inside goroutine
go func() {
    wg.Add(1)  // Race condition — may run after Wait()
    defer wg.Done()
    doWork()
}()

// CORRECT: Add before launching goroutine
wg.Add(1)
go func() {
    defer wg.Done()
    doWork()
}()

// WRONG: Not using defer for Unlock
func (c *SafeCounter) Increment() {
    c.mu.Lock()
    c.count++  // If this panics, mutex is never unlocked!
    c.mu.Unlock()
}

// CORRECT: defer Unlock
func (c *SafeCounter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.count++
}

// WRONG: Using Mutex when RWMutex is better
type Cache struct {
    mu   sync.Mutex  // All operations are exclusive
    data map[string]string
}

// CORRECT: Use RWMutex for read-heavy workloads
type Cache struct {
    mu   sync.RWMutex  // Multiple readers allowed
    data map[string]string
}
```

## Gotchas
- `wg.Add(1)` must be called BEFORE `go func()` — race condition otherwise
- `errgroup` cancels the context when any goroutine returns an error
- `errgroup.SetLimit()` controls max concurrent goroutines (Go 1.20+)
- `sync.Once` is goroutine-safe — multiple goroutines can call `Do()`, only one runs
- `sync.RWMutex` allows multiple concurrent readers but exclusive writers
- `sync.Pool` is for object reuse, not caching — objects may be garbage collected
- Never copy a `sync.Mutex` (pass by pointer, not by value)
- `context.WithCancel` in errgroup cancels all goroutines when one fails

## Related
- go/stdlib/goroutines.md
- go/stdlib/channels.md
- go/stdlib/context.md
