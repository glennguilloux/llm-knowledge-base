---
id: "go-concurrency-context-cancellation"
title: "Go Context Cancellation"
language: "go"
category: "concurrency"
subcategory: "context"
tags: ["go", "context", "cancellation", "timeout", "deadline", "graceful shutdown", "request context"]
version: "1.21+"
retrieval_hint: "Go context cancellation timeout graceful shutdown WithCancel WithTimeout request context"
last_verified: "2026-06-20"
confidence: "medium"
---

# Go Context Cancellation

## When to Use
- Cancelling in-flight work when a caller gives up
- Applying request, operation, or deadline limits
- Coordinating shutdown across goroutines
- Propagating cancellation through library and service boundaries
- Cleaning up resources after timed-out or cancelled operations

## Standard Pattern

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	if err := Run(ctx); err != nil && !errors.Is(err, context.Canceled) {
		fmt.Println("run failed:", err)
	}
}

func Run(parent context.Context) error {
	ctx, cancel := context.WithCancel(parent)
	defer cancel()

	workerCtx, stop := context.WithTimeout(ctx, 500*time.Millisecond)
	defer stop()

	return processBatch(workerCtx, []string{"alpha", "beta", "gamma"})
}

func processBatch(ctx context.Context, items []string) error {
	for _, item := range items {
		if err := ctx.Err(); err != nil {
			return err
		}
		if err := processItem(ctx, item); err != nil {
			if ctx.Err() != nil {
				return ctx.Err()
			}
			return err
		}
	}
	return nil
}

func processItem(ctx context.Context, item string) error {
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
		return doWork(item)
	}
}

func doWork(item string) error {
	_ = item
	return nil
}
```

## Common Mistakes

```go
// WRONG: Forgetting to call the cancel function
func leakyTimeout() error {
	ctx, _ := context.WithTimeout(context.Background(), time.Second)
	return processBatch(ctx, []string{"one"})
}

// CORRECT: Always call cancel, usually with defer
func boundedTimeout() error {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	return processBatch(ctx, []string{"one"})
}

// WRONG: Replacing a request context with Background inside a handler
func wrongRequestContext() error {
	return queryDatabase(context.Background())
}

// CORRECT: Carry the caller's context through the call chain
func correctRequestContext(ctx context.Context) error {
	return queryDatabase(ctx)
}

// WRONG: Starting a goroutine that cannot observe cancellation
func wrongBackgroundLoop(ctx context.Context) {
	go func() {
		for {
			refreshCache()
		}
	}()
}

// CORRECT: Exit when the context is cancelled
func correctBackgroundLoop(ctx context.Context) {
	go func() {
		for {
			select {
			case <-ctx.Done():
				return
			default:
				refreshCache()
			}
		}
	}()
}

// WRONG: Returning nil after cancellation hides why work stopped
func wrongCancelError(ctx context.Context) error {
	<-ctx.Done()
	return nil
}

// CORRECT: Return ctx.Err so callers can distinguish cancellation from success
func correctCancelError(ctx context.Context) error {
	<-ctx.Done()
	return ctx.Err()
}

// WRONG: Storing request context in a long-lived struct
type wrongServer struct {
	ctx context.Context
}

// CORRECT: Pass context as an explicit argument
type correctServer struct{}

func (s *correctServer) Handle(ctx context.Context) error {
	return processBatch(ctx, []string{"request"})
}

func queryDatabase(ctx context.Context) error {
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
		return nil
	}
}

func refreshCache() {}
```

## Gotchas
- Always call the cancel function returned by `context.WithCancel`, `WithTimeout`, or `WithDeadline`.
- Pass the caller's context as the first argument to functions that perform I/O or start work.
- Do not store request contexts in structs; contexts are request-scoped values, not configuration.
- Use `context.Cause` when wrapping cancellation with richer error information in Go 1.20+.
- A cancelled context should normally be returned as `context.Canceled` or `context.DeadlineExceeded`, not as success.
- Context values are for request metadata; they should not replace explicit function parameters.
- Long-running goroutines need a cancellation path, usually by selecting on `ctx.Done()`.
- `context.Background()` is appropriate for `main`, tests, and top-level callers, not inside request handlers.

## Related
- go/concurrency/patterns.md
- go/concurrency/sync-patterns.md
- go/stdlib/context.md
- go/stdlib/goroutines.md
