---
id: "go-stdlib-context"
title: "Context and Cancellation"
language: "go"
category: "stdlib"
tags: ["go", "context", "cancel", "timeout", "deadline", "propagation"]
version: "1.21+"
retrieval_hint: "context cancel timeout deadline WithCancel WithTimeout"
last_verified: "2026-05-22"
confidence: "high"
---

# Context and Cancellation

## When to Use
- Propagating cancellation through call chains
- Setting deadlines on operations
- Passing request-scoped values (request ID, auth token)
- Graceful shutdown of long-running operations

## Standard Pattern

```go
package main

import (
	"context"
	"fmt"
	"time"
)

// Basic context with cancellation
func example1() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel() // Always call cancel to release resources

	go func() {
		// Simulate work
		time.Sleep(2 * time.Second)
		cancel() // Signal cancellation
	}()

	select {
	case <-ctx.Done():
		fmt.Println("Cancelled:", ctx.Err())
	case result := <-doWork(ctx):
		fmt.Println("Result:", result)
	}
}

// Context with timeout
func example2() {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	result, err := fetchData(ctx)
	if err != nil {
		fmt.Println("Error:", err) // Likely deadline exceeded
		return
	}
	fmt.Println("Result:", result)
}

// Context with deadline
func example3() {
	deadline := time.Now().Add(10 * time.Second)
	ctx, cancel := context.WithDeadline(context.Background(), deadline)
	defer cancel()

	// All operations using ctx will be cancelled after deadline
	processWithContext(ctx)
}

// Context with values (request-scoped)
func example4() {
	ctx := context.WithValue(context.Background(), "request_id", "abc-123")
	ctx = context.WithValue(ctx, "user_id", 42)

handleRequest(ctx)
}

func handleRequest(ctx context.Context) {
	reqID := ctx.Value("request_id").(string)
	userID := ctx.Value("user_id").(int)
	fmt.Printf("Request %s from user %d\n", reqID, userID)
}

// Checking context in loops
func processItems(ctx context.Context, items []Item) error {
	for _, item := range items {
		select {
		case <-ctx.Done():
			return ctx.Err() // Return immediately on cancellation
		default:
			// Continue processing
		}
		if err := process(item); err != nil {
			return err
		}
	}
	return nil
}

type Item struct{}
func process(Item) error { return nil }
func doWork(ctx context.Context) <-chan string { return nil }
func fetchData(ctx context.Context) (string, error) { return "", nil }
func processWithContext(ctx context.Context) {}
```

## Common Mistakes

```go
// WRONG: Not calling cancel (resource leak)
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
// Missing defer cancel() — context leaks until timeout

// CORRECT: Always defer cancel
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

// WRONG: Passing context.Background() instead of request context
func handler(w http.ResponseWriter, r *http.Request) {
	data, _ := queryDatabase(context.Background()) // Ignores request cancellation
}

// CORRECT: Use request context
func handler(w http.ResponseWriter, r *http.Request) {
	data, _ := queryDatabase(r.Context())
}

// WRONG: Storing context in a struct
type Server struct {
	ctx context.Context // Anti-pattern — context per request
}

// CORRECT: Pass context as first parameter
func (s *Server) Handle(ctx context.Context, req Request) error {
	// Context flows through function calls
}

// WRONG: Ignoring ctx.Err()
func process(ctx context.Context) error {
	<-ctx.Done()
	return nil // Doesn't tell caller why it was cancelled
}

// CORRECT: Return context error
func process(ctx context.Context) error {
	<-ctx.Done()
	return ctx.Err() // context.Canceled or context.DeadlineExceeded
}
```

## Gotchas
- `context.Background()` is the root context — use for main, init, and tests
- `context.TODO()` is a placeholder — use when unsure which context to use
- `WithCancel`, `WithTimeout`, `WithDeadline` return a cancel function — ALWAYS call it
- Not calling `cancel()` leaks resources until the parent context is done
- Context values are for request-scoped data, not for optional parameters
- `ctx.Value()` returns `any` — type assert immediately, don't store
- `ctx.Err()` returns `nil` while context is active, `Canceled` or `DeadlineExceeded` after done
- Context is immutable — `WithValue` creates a new context, doesn't modify the parent
- HTTP handlers get context from `r.Context()` — it's cancelled when the client disconnects
- `select` on `ctx.Done()` is the idiomatic way to check for cancellation

## Related
- go/stdlib/goroutines.md
- go/stdlib/channels.md
- go/web/http-server.md
