---
id: "go-concurrency-goroutines"
title: "Goroutines and Concurrency"
language: "go"
category: "concurrency"
tags: ["go", "goroutine", "concurrency", "waitgroup", "parallel"]
version: "1.21+"
retrieval_hint: "goroutine go keyword WaitGroup concurrency parallel"
last_verified: "2026-05-22"
confidence: "high"
---

# Goroutines and Concurrency

## When to Use
- Running tasks concurrently (HTTP requests, file processing)
- Background workers and job processors
- Parallel data processing pipelines
- Non-blocking I/O operations

## Standard Pattern

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

// Basic goroutine
func worker(id int) {
	fmt.Printf("Worker %d starting\n", id)
	time.Sleep(time.Second)
	fmt.Printf("Worker %d done\n", id)
}

func main() {
	// Launch goroutines
	go worker(1)
	go worker(2)
	time.Sleep(2 * time.Second) // BAD: use WaitGroup instead

	// Proper synchronization with WaitGroup
	var wg sync.WaitGroup
	for i := 1; i <= 5; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			worker(id)
		}(i)
	}
	wg.Wait() // Block until all workers complete

	// Goroutine with error handling
	type result struct {
		value int
		err   error
	}

	results := make(chan result, 5)
for i := 1; i <= 5; i++ {
		go func(id int) {
			v, err := doWork(id)
			results <- result{v, err}
		}(i)
	}

	for i := 0; i < 5; i++ {
		r := <-results
		if r.err != nil {
			fmt.Printf("Error: %v\n", r.err)
			continue
		}
		fmt.Printf("Result: %d\n", r.value)
	}
}

func doWork(id int) (int, error) {
	return id * 2, nil
}
```

## Common Mistakes

```go
// WRONG: Goroutine leak — no way to stop
func leak() {
	go func() {
		for {
			// Runs forever — no exit condition
			process()
		}
	}()
}

// CORRECT: Use context for cancellation
func noLeak(ctx context.Context) {
	go func() {
		for {
			select {
			case <-ctx.Done():
				return // Graceful exit
			default:
				process()
			}
		}
	}()
}

// WRONG: Loop variable capture in goroutine
for i := 0; i < 5; i++ {
	go func() {
		fmt.Println(i) // All print 5 (or unpredictable)
	}()
}

// CORRECT: Pass as parameter
for i := 0; i < 5; i++ {
	go func(id int) {
		fmt.Println(id) // Prints 0,1,2,3,4
	}(i)
}

// WRONG: Using time.Sleep for synchronization
go doWork()
time.Sleep(time.Second) // Race condition — may finish early or late

// CORRECT: Use WaitGroup or channel
var wg sync.WaitGroup
wg.Add(1)
go func() {
	defer wg.Done()
	doWork()
}()
wg.Wait()

// WRONG: Starting too many goroutines
for _, item := range millionItems {
	go process(item) // 1 million goroutines — OOM
}

// CORRECT: Use worker pool
const workers = 10
jobs := make(chan Item, workers)
var wg sync.WaitGroup

for i := 0; i < workers; i++ {
	wg.Add(1)
	go func() {
		defer wg.Done()
		for item := range jobs {
			process(item)
		}
	}()
}
for _, item := range millionItems {
	jobs <- item
}
close(jobs)
wg.Wait()
```

## Gotchas
- Goroutines are cheap (~2KB stack) but not free — millions can exhaust memory
- Loop variable capture: the goroutine may see the loop variable's final value, not the value at creation
- `sync.WaitGroup` methods (`Add`, `Done`, `Wait`) must be called correctly — `Add` before `go`
- Goroutines that block forever are leaks — use `context.Context` for cancellation
- `runtime.GOMAXPROCS` defaults to number of CPU cores — rarely need to change
- `defer` in a goroutine runs when that goroutine exits, not when the parent function returns
- Panics in goroutines crash the entire program — use `recover` in each goroutine
- `fmt.Println` is not goroutine-safe for structured output — use a logger or channel

## Related
- go/stdlib/channels.md
- go/stdlib/context.md
- go/concurrency/patterns.md
