---
id: "go-concurrency-patterns"
title: "Concurrency Patterns"
language: "go"
category: "concurrency"
tags: ["go", "concurrency", "worker-pool", "pipeline", "fan-out", "sync.Once", "sync.Pool", "rate-limit"]
version: "1.21+"
retrieval_hint: "worker pool pipeline fan-out rate limit sync.Once sync.Pool mutex race"
last_verified: "2026-05-24"
confidence: "high"
---

# Concurrency Patterns

## When to Use
- Processing many items concurrently with bounded parallelism
- Building data processing pipelines with stages
- Implementing rate limiting for API calls
- Lazy initialization with thread safety (sync.Once)
- Object pooling to reduce GC pressure (sync.Pool)
- Protecting shared state (Mutex)

## Standard Pattern

```go
package main

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"time"
)

// === Worker Pool ===
type Job struct {
	ID   int
	Data string
}

type Result struct {
	JobID int
	Output string
	Err   error
}

func workerPool(ctx context.Context, numWorkers int, jobs <-chan Job) <-chan Result {
	results := make(chan Result, numWorkers)
	var wg sync.WaitGroup

	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for job := range jobs {
				select {
				case <-ctx.Done():
					return
				default:
					output, err := processJob(job)
					results <- Result{JobID: job.ID, Output: output, Err: err}
				}
			}
		}(i)
	}

	go func() {
		wg.Wait()
		close(results)
	}()

	return results
}

// === Pipeline ===
func generate(ctx context.Context, nums ...int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for _, n := range nums {
			select {
			case out <- n:
			case <-ctx.Done():
				return
			}
		}
	}()
	return out
}

func square(ctx context.Context, in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for n := range in {
			select {
			case out <- n * n:
			case <-ctx.Done():
				return
			}
		}
	}()
	return out
}

func filterEven(ctx context.Context, in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for n := range in {
			if n%2 == 0 {
				select {
				case out <- n:
				case <-ctx.Done():
					return
				}
			}
		}
	}()
	return out
}

// Usage: generate(1,2,3,4,5) → square → filterEven → consume

// === Fan-Out / Fan-In ===
func fanOut(ctx context.Context, input <-chan int, workers int) []<-chan int {
	channels := make([]<-chan int, workers)
	for i := 0; i < workers; i++ {
		channels[i] = square(ctx, input) // each reads from same input
	}
	return channels
}

func fanIn(ctx context.Context, channels ...<-chan int) <-chan int {
	var wg sync.WaitGroup
	merged := make(chan int)

	for _, ch := range channels {
		wg.Add(1)
		go func(c <-chan int) {
			defer wg.Done()
			for v := range c {
				select {
				case merged <- v:
				case <-ctx.Done():
					return
				}
			}
		}(ch)
	}

	go func() {
		wg.Wait()
		close(merged)
	}()

	return merged
}

// === Rate Limiter with time.Ticker ===
func rateLimitedAPICall(urls []string) {
	ticker := time.NewTicker(100 * time.Millisecond) // 10 req/sec
	defer ticker.Stop()

	for _, url := range urls {
		<-ticker.C // wait for tick
		go func(u string) {
			http.Get(u)
		}(url)
	}
}

// Token bucket alternative using buffered channel
func newTokenBucket(rate int) chan struct{} {
	ch := make(chan struct{}, rate)
	go func() {
		for {
			time.Sleep(time.Second / time.Duration(rate))
			ch <- struct{}{}
		}
	}()
	return ch
}

// === sync.Once — thread-safe lazy init ===
var (
	config *Config
	configOnce sync.Once
)

func GetConfig() *Config {
	configOnce.Do(func() {
		config = loadConfig() // runs exactly once, even with concurrent calls
	})
	return config
}

// === sync.Pool — reduce allocations ===
var bufferPool = sync.Pool{
	New: func() any {
		return make([]byte, 0, 4096)
	},
}

func process(data []byte) {
	buf := bufferPool.Get().([]byte)[:0] // get from pool, reset length
	defer bufferPool.Put(buf)            // return to pool

	buf = append(buf, data...)
	// use buf...
}

// === Mutex — protect shared state ===
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

// RWMutex — many readers, few writers
type SafeCache struct {
	mu    sync.RWMutex
	items map[string]string
}

func (c *SafeCache) Get(key string) (string, bool) {
	c.mu.RLock()         // multiple readers allowed
	defer c.mu.RUnlock()
	v, ok := c.items[key]
	return v, ok
}

func (c *SafeCache) Set(key, val string) {
	c.mu.Lock()          // exclusive write lock
	defer c.mu.Unlock()
	c.items[key] = val
}

// Stubs
func processJob(j Job) (string, error) { return j.Data, nil }
type Config struct{}
func loadConfig() *Config { return &Config{} }
```

## Common Mistakes

```go
// WRONG: race condition — unsynchronized map access
var cache = map[string]string{}

// goroutine 1
cache["key"] = "value"

// goroutine 2
val := cache["key"]  // DATA RACE — undefined behavior

// CORRECT: protect with mutex
var mu sync.RWMutex
mu.Lock()
cache["key"] = "value"
mu.Unlock()

// WRONG: unbuffered channel with no receiver — goroutine leak
func startWorker() <-chan Result {
    ch := make(chan Result)  // unbuffered
    go func() {
        result := doWork()
        ch <- result  // blocks if nobody reads — goroutine leaks
    }()
    return ch
}

// CORRECT: buffered or context-cancellable
func startWorker(ctx context.Context) <-chan Result {
    ch := make(chan Result, 1)  // buffered
    go func() {
        result := doWork()
        select {
        case ch <- result:
        case <-ctx.Done():  // don't leak if nobody reads
        }
    }()
    return ch
}

// WRONG: using sync.Mutex for read-heavy workloads
func (c *SafeCache) Get(key string) string {
    c.mu.Lock()  // exclusive — blocks all other reads
    defer c.mu.Unlock()
    return c.items[key]
}

// CORRECT: use RWMutex for read-heavy
func (c *SafeCache) Get(key string) string {
    c.mu.RLock()  // shared — allows concurrent reads
    defer c.mu.RUnlock()
    return c.items[key]
}

// WRONG: not draining results from pipeline — workers stall
results := workerPool(ctx, 5, jobs)
// forgot to consume results → workers block on send

// CORRECT: always consume or discard
for result := range results {
    handle(result)
}

// WRONG: race detected by -race flag but ignored
// data race in counter++
counter++
// Use `go test -race` to find these

// CORRECT: use atomic or mutex
var counter atomic.Int64
counter.Add(1)
```

## Gotchas
- `go test -race` enables the race detector — catches data races at runtime but adds overhead
- Worker pool: numWorkers controls parallelism — too many wastes resources, too few underutilizes
- Pipeline stages should be context-aware — cancel all stages when the pipeline is cancelled
- `sync.Once.Do` blocks until the function completes — concurrent callers all wait
- `sync.Pool` objects can be GC'd between `Get` and `Put` — don't assume persistence
- `sync.Pool` is per-P (per-processor) — reduces contention, but Get may return from any P
- `Mutex` is not reentrant — a goroutine that holds the lock and tries to lock again will deadlock
- `RWMutex` starvation: many readers can starve writers — Go's implementation favors writers
- Channel direction (`chan<-`, `<-chan`) prevents accidental sends/receives at compile time
- `close(ch)` on a closed channel panics — only the sender should close, and only once
- `select` with multiple ready channels picks one pseudo-randomly — not FIFO
- `context.WithCancel` must have `defer cancel()` called — otherwise resources leak
- Never start a goroutine without a way to stop it — use context, done channel, or WaitGroup

## Related
- go/stdlib/goroutines.md
- go/stdlib/channels.md
- go/stdlib/context.md
