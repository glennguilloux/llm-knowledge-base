---
id: "go-concurrency-channels-patterns"
title: "Go Channel Patterns and Select Multiplexing"
language: "go"
category: "concurrency"
subcategory: "channels"
tags: ["go", "channels", "channel", "buffered", "unbuffered", "select", "select-multiplexing", "fan-in", "fan in", "fan-out", "fan out", "worker-pool", "worker pool", "producer-consumer"]
version: "1.21+"
retrieval_hint: "Go channels select fan in fan out worker pool channel patterns select multiplexing buffered unbuffered close ownership producer-consumer"
last_verified: "2026-06-20"
confidence: "medium"
---

# Go Channel Patterns

## When to Use
- Moving work between goroutines with explicit synchronization
- Building producer-consumer pipelines with bounded memory use
- Merging multiple worker outputs into one result stream
- Splitting one input stream across several workers
- Signaling completion or cancellation with a closed or done channel

## Standard Pattern

```go
package main

import "context"

type Job struct {
	ID   int
	Name string
}

type Result struct {
	JobID int
	Value string
	Err   error
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	jobs := make(chan Job, 8)
	results := make(chan Result, 8)
	merged := make(chan Result)

	go produceJobs(ctx, jobs, []Job{{ID: 1, Name: "a"}, {ID: 2, Name: "b"}})
	go processJobs(ctx, jobs, results)
	go mergeResults(ctx, results, merged)

	for result := range merged {
		_ = result
	}
}

func produceJobs(ctx context.Context, out chan<- Job, jobs []Job) {
	defer close(out)
	for _, job := range jobs {
		select {
		case out <- job:
		case <-ctx.Done():
			return
		}
	}
}

func processJobs(ctx context.Context, in <-chan Job, out chan<- Result) {
	defer close(out)
	for {
		select {
		case <-ctx.Done():
			return
		case job, ok := <-in:
			if !ok {
				return
			}
			result := doWork(ctx, job)
			select {
			case out <- result:
			case <-ctx.Done():
				return
			}
		}
	}
}

func mergeResults(ctx context.Context, in <-chan Result, out chan<- Result) {
	defer close(out)
	for {
		select {
		case <-ctx.Done():
			return
		case result, ok := <-in:
			if !ok {
				return
			}
			select {
			case out <- result:
			case <-ctx.Done():
				return
			}
		}
	}
}

func doWork(ctx context.Context, job Job) Result {
	select {
	case <-ctx.Done():
		return Result{JobID: job.ID, Err: ctx.Err()}
	default:
		return Result{JobID: job.ID, Value: job.Name}
	}
}
```

## Common Mistakes

```go
// WRONG: Receiver closes a channel that the producer still sends on
func wrongClose(out chan int) {
	close(out)
	out <- 1 // panic: send on closed channel
}

// CORRECT: Only the goroutine that owns sending closes the channel
func correctClose(out chan<- int) {
	defer close(out)
	out <- 1
}

// WRONG: Blocking send can leak a goroutine when nobody receives
func startBlocked() <-chan int {
	out := make(chan int)
	go func() {
		out <- expensiveWork() // blocks forever if caller never reads
	}()
	return out
}

// CORRECT: Make the send cancellable or use a bounded buffer
func startCancellable(ctx context.Context) <-chan int {
	out := make(chan int, 1)
	go func() {
		defer close(out)
		select {
		case out <- expensiveWork():
		case <-ctx.Done():
		}
	}()
	return out
}

// WRONG: Range over a channel that is never closed
func neverClosed() <-chan int {
	out := make(chan int)
	go func() {
		out <- 1
		out <- 2
		// missing close(out)
	}()
	return out
}

// CORRECT: Close after all sends finish, and never send after close
func properlyClosed() <-chan int {
	out := make(chan int, 2)
	go func() {
		defer close(out)
		out <- 1
		out <- 2
	}()
	return out
}

// WRONG: Treating nil and closed channels as the same state
func nilOrClosed(ch <-chan int) int {
	return <-ch // nil blocks forever; closed returns zero immediately
}

// CORRECT: Initialize channels and detect closed channels with ok
func receiveWithOK(ch <-chan int) (int, bool) {
	if ch == nil {
		return 0, false
	}
	v, ok := <-ch
	return v, ok
}

func expensiveWork() int { return 42 }
```

## Gotchas
- Unbuffered channels synchronize sender and receiver at the moment of communication.
- Buffered channels decouple send and receive only up to their capacity; full sends and empty receives still block.
- Closing a channel is a broadcast signal from sender to receivers, not a mutex or a data-clearing operation.
- Only the sender should close a channel, and it must close it at most once.
- Receivers can detect closure with `value, ok := <-ch`; ranging exits when the channel closes.
- Nil channels are always inactive in `select`; assign `nil` to disable a case after EOF.
- Directional channel types (`chan<- T` and `<-chan T`) prevent accidental sends or receives at compile time.
- A goroutine blocked sending to an unbuffered channel can leak unless the send is cancellable or buffered.

## Related
- go/concurrency/patterns.md
- go/concurrency/sync-patterns.md
- go/stdlib/channels.md
- go/patterns/fan-in.md
- go/patterns/fan-out.md
