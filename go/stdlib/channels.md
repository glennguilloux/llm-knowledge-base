---
id: "go-concurrency-channels"
title: "Channels and Communication"
language: "go"
category: "concurrency"
tags: ["go", "channel", "select", "buffered", "unbuffered", "concurrency"]
version: "1.21+"
retrieval_hint: "channel buffered unbuffered select close range"
last_verified: "2026-05-22"
confidence: "high"
---

# Channels and Communication

## When to Use
- Communicating between goroutines
- Implementing producer-consumer patterns
- Coordinating concurrent work
- Building pipelines

## Standard Pattern

```go
package main

import (
	"fmt"
	"time"
)

// Unbuffered channel — synchronous (sender blocks until receiver)
ch := make(chan int)

// Buffered channel — asynchronous up to capacity
buffered := make(chan string, 10)

// Send and receive
ch <- 42      // Send
value := <-ch // Receive

// Channel with range
func producer(ch chan<- int) {
	for i := 0; i < 5; i++ {
		ch <- i
	}
	close(ch) // Signal no more values
}

func consumer(ch <-chan int) {
	for value := range ch { // Exits when channel is closed
		fmt.Println(value)
	}
}

// Select statement — multiplex channels
func multiplex(ch1, ch2 <-chan int, done <-chan struct{}) {
	for {
		select {
		case v, ok := <-ch1:
			if !ok {
				ch1 = nil // Disable this case
				continue
			}
			fmt.Println("ch1:", v)
		case v, ok := <-ch2:
			if !ok {
				ch2 = nil
				continue
			}
			fmt.Println("ch2:", v)
		case <-done:
			fmt.Println("done")
			return
		case <-time.After(5 * time.Second):
			fmt.Println("timeout")
			return
		}
	}
}

// Directional channels (compile-time safety)
func send(ch chan<- int, value int) { ch <- value }
func recv(ch <-chan int) int { return <-ch }

// Done channel pattern
done := make(chan struct{})
go func() {
	defer close(done) // Signal completion
	// do work
}()
<-done // Wait for completion
```

## Common Mistakes

```go
// WRONG: Sending on closed channel (panics)
close(ch)
ch <- 42 // panic: send on closed channel

// CORRECT: Only sender should close
// Receiver never closes — only the sender closes

// WRONG: Forgetting to close channel (range hangs)
ch := make(chan int)
go func() {
	for i := 0; i < 5; i++ {
		ch <- i
	}
	// Missing close(ch) — range loop never exits
}()
for v := range ch {
	fmt.Println(v)
}

// CORRECT: Close channel when done sending
go func() {
	for i := 0; i < 5; i++ {
		ch <- i
	}
	close(ch)
}()

// WRONG: Unbuffered channel with no receiver (deadlock)
ch := make(chan int)
ch <- 42 // Blocks forever — no receiver

// CORRECT: Use buffered or ensure receiver exists
ch := make(chan int, 1)
ch <- 42 // OK — buffered

// WRONG: Using nil channel (blocks forever)
var ch chan int
ch <- 42  // Blocks forever
v := <-ch // Blocks forever

// CORRECT: Initialize channel
ch := make(chan int)

// WRONG: Not draining channel on exit
func worker(ch <-chan int) {
	for {
		select {
		case v := <-ch:
			process(v)
		// No default or done — leaks if channel never closed
		}
	}
}
```

## Gotchas
- Unbuffered channels block until both sender and receiver are ready — rendezvous point
- Buffered channels block only when full (send) or empty (receive)
- `close(ch)` signals "no more values" — `range` exits, `v, ok := <-ch` gets `ok=false`
- Only the sender should close a channel — closing a closed channel panics
- `select` with no `default` blocks until one case is ready
- `select` with `default` is non-blocking — polls channels
- `time.After` returns a channel — use in `select` for timeouts
- Nil channels block forever — useful for disabling `select` cases
- Channel direction (`chan<-` send-only, `<-chan` receive-only) catches bugs at compile time
- `for range ch` exits when the channel is closed AND drained

## Related
- go/stdlib/goroutines.md
- go/stdlib/context.md
- go/concurrency/patterns.md
