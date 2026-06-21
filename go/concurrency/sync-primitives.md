---
id: "go-concurrency-sync-primitives"
title: "Go Sync Primitives: Mutex, RWMutex, Cond, WaitGroup"
language: "go"
category: "concurrency"
subcategory: "sync"
tags: ["go", "sync", "primitives", "mutex", "RWMutex", "Cond", "WaitGroup", "Once", "atomic"]
version: "1.21+"
retrieval_hint: "Go sync primitives mutex RWMutex Cond WaitGroup Once atomic race"
last_verified: "2026-06-20"
confidence: "medium"
---

# Go Sync Primitives: Mutex, RWMutex, Cond, WaitGroup

## When to Use
- Protecting shared mutable state across goroutines
- Waiting for a fixed set of goroutines to finish
- Allowing many readers with exclusive writes
- Coordinating goroutines that wait for a condition to become true
- Performing one-time initialization safely

## Standard Pattern

```go
package main

import (
	"context"
	"sync"
	"sync/atomic"
)

func main() {
	cache := NewSafeCache()
	cache.Set("mode", "prod")
	_, _ = cache.Get("mode")

	counter := &Counter{}
	counter.Add(2)

	gate := NewGate()
	gate.Open()
	gate.WaitUntilOpen()

	_ = LoadConfig()
	_ = WaitAll(context.Background(), []string{"alpha", "beta"})
}

type SafeCache struct {
	mu   sync.RWMutex
	data map[string]string
}

func NewSafeCache() *SafeCache {
	return &SafeCache{data: make(map[string]string)}
}

func (c *SafeCache) Get(key string) (string, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	value, ok := c.data[key]
	return value, ok
}

func (c *SafeCache) Set(key, value string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.data[key] = value
}

type Counter struct {
	value atomic.Int64
}

func (c *Counter) Add(delta int64) int64 {
	return c.value.Add(delta)
}

func (c *Counter) Load() int64 {
	return c.value.Load()
}

type Gate struct {
	mu   sync.Mutex
	cond *sync.Cond
	open bool
}

func NewGate() *Gate {
	gate := &Gate{}
	gate.cond = sync.NewCond(&gate.mu)
	return gate
}

func (g *Gate) WaitUntilOpen() {
	g.mu.Lock()
	defer g.mu.Unlock()
	for !g.open {
		g.cond.Wait()
	}
}

func (g *Gate) Open() {
	g.mu.Lock()
	g.open = true
	g.mu.Unlock()
	g.cond.Broadcast()
}

var (
	configOnce sync.Once
	config     Config
)

type Config struct {
	Mode string
}

func LoadConfig() Config {
	configOnce.Do(func() {
		config = Config{Mode: "prod"}
	})
	return config
}

func WaitAll(ctx context.Context, urls []string) error {
	var wg sync.WaitGroup
	errCh := make(chan error, len(urls))

	for _, url := range urls {
		wg.Add(1)
		go func(url string) {
			defer wg.Done()
			select {
			case <-ctx.Done():
				errCh <- ctx.Err()
			default:
				errCh <- fetch(url)
			}
		}(url)
	}

	done := make(chan struct{})
	go func() {
		wg.Wait()
		close(done)
	}()

	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-done:
		close(errCh)
		for err := range errCh {
			if err != nil {
				return err
			}
		}
		return nil
	}
}

func fetch(url string) error {
	_ = url
	return nil
}
```

## Common Mistakes

```go
// WRONG: Calling WaitGroup.Add after starting the goroutine
func wrongWaitGroup() {
	var wg sync.WaitGroup
	go func() {
		wg.Add(1)
		defer wg.Done()
		doWork()
	}()
	wg.Wait()
}

// CORRECT: Add before launching the goroutine
func correctWaitGroup() {
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		doWork()
	}()
	wg.Wait()
}

// WRONG: Unlocking without defer can leave a mutex locked after panic
func wrongMutex(counter *int) {
	var mu sync.Mutex
	mu.Lock()
	*counter = *counter + 1
	mu.Unlock()
}

// CORRECT: Unlock with defer immediately after Lock
func correctMutex(counter *int) {
	var mu sync.Mutex
	mu.Lock()
	defer mu.Unlock()
	*counter = *counter + 1
}

// WRONG: Copying a mutex after first use breaks synchronization
type wrongHolder struct {
	mu sync.Mutex
	n  int
}

func copyWrong(holder wrongHolder) wrongHolder {
	return holder
}

// CORRECT: Pass mutex-protected values by pointer
type correctHolder struct {
	mu sync.Mutex
	n  int
}

func copyCorrect(holder *correctHolder) *correctHolder {
	return holder
}

// WRONG: Updating a shared integer with ++ from many goroutines
func wrongAtomic(counter *int64) {
	*counter = *counter + 1
}

// CORRECT: Use atomic types for standalone counters
func correctAtomic(counter *atomic.Int64) {
	counter.Add(1)
}

// WRONG: Signalling a Cond without holding its Locker
func wrongCond(gate *Gate) {
	gate.cond.Broadcast() // data race on gate.open
}

// CORRECT: Change the guarded state while holding the lock, then signal
func correctCond(gate *Gate) {
	gate.mu.Lock()
	gate.open = true
	gate.mu.Unlock()
	gate.cond.Broadcast()
}

func doWork() {}
```

## Gotchas
- `WaitGroup.Add` must happen before the corresponding goroutine starts.
- `Mutex` and `RWMutex` must not be copied after first use; pass the containing value by pointer.
- Prefer `defer Unlock()` immediately after `Lock()` to keep critical sections correct during panics.
- Use `RWMutex` when reads greatly outnumber writes; use `Mutex` when writes are common or the protected state is small.
- `sync.Cond` requires holding the associated locker when changing the condition and when calling `Wait`.
- `sync.Once` runs its function once per `Once` value; concurrent callers block until it completes.
- `atomic.Int64` is ideal for counters and flags, but complex invariants still need a mutex.
- A goroutine waiting on `Cond.Wait` releases the lock while waiting and reacquires it before returning.

## Related
- go/concurrency/patterns.md
- go/concurrency/sync-patterns.md
- go/stdlib/goroutines.md
- go/stdlib/channels.md
