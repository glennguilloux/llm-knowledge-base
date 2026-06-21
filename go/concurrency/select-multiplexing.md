---
id: "go-concurrency-select-multiplexing"
title: "Go Select Multiplexing"
language: "go"
category: "concurrency"
subcategory: "select"
tags: ["go", "select", "multiplexing", "channels", "nonblocking", "timeout", "fan-in"]
version: "1.21+"
retrieval_hint: "Go select multiplexing channels nonblocking timeout fan-in cancellation"
last_verified: "2026-06-20"
confidence: "medium"
---

# Go Select Multiplexing

## When to Use
- Waiting on multiple channels at the same time
- Adding cancellation or timeout cases to sends and receives
- Implementing non-blocking polls with a `default` case
- Merging several input streams into one output stream
- Disabling closed channels by assigning them to `nil`

## Standard Pattern

```go
package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	urgent := make(chan string, 1)
	normal := make(chan string, 1)
	urgent <- "urgent"
	close(urgent)
	close(normal)

	msg, ok := NextMessage(ctx, urgent, normal)
	if ok {
		fmt.Println(msg)
	}

	intUrgent := make(chan int, 1)
	intNormal := make(chan int, 1)
	intUrgent <- 1
	close(intUrgent)
	close(intNormal)

	merged := Merge(ctx, intUrgent, intNormal)
	for value := range merged {
		_ = value
	}
}

func NextMessage(ctx context.Context, urgent <-chan string, normal <-chan string) (string, bool) {
	select {
	case <-ctx.Done():
		return "", false
	case msg := <-urgent:
		return msg, true
	case msg := <-normal:
		return msg, true
	}
}

func TrySend[T any](ch chan<- T, value T) bool {
	select {
	case ch <- value:
		return true
	default:
		return false
	}
}

func Merge(ctx context.Context, inputs ...<-chan int) <-chan int {
	out := make(chan int)
	var wg sync.WaitGroup

	for _, in := range inputs {
		wg.Add(1)
		go func(ch <-chan int) {
			defer wg.Done()
			for {
				select {
				case <-ctx.Done():
					return
				case value, ok := <-ch:
					if !ok {
						return
					}
					select {
					case out <- value:
					case <-ctx.Done():
						return
					}
				}
			}
		}(in)
	}

	go func() {
		wg.Wait()
		close(out)
	}()

	return out
}

func DrainWithTimer(ch <-chan int, timeout time.Duration) {
	timer := time.NewTimer(timeout)
	defer timer.Stop()

	for {
		select {
		case _, ok := <-ch:
			if !ok {
				return
			}
		case <-timer.C:
			return
		}
	}
}
```

## Common Mistakes

```go
// WRONG: Busy polling with default spins the CPU
func busyPoll(ch <-chan int) int {
	for {
		select {
		case v := <-ch:
			return v
		default:
			// no pause: wastes CPU
		}
	}
}

// CORRECT: Use a timer or wait on another channel when no work is ready
func timedPoll(ch <-chan int, tick <-chan time.Time) int {
	for {
		select {
		case v := <-ch:
			return v
		case <-tick:
			// retry later without spinning
		}
	}
}

// WRONG: Creating a new timer in a tight select loop can leak timer resources
func wrongTimerLoop(ch <-chan int) int {
	for {
		select {
		case v := <-ch:
			return v
		case <-time.After(time.Millisecond):
			return 0
		}
	}
}

// CORRECT: Reuse one timer and stop it when finished
func correctTimerLoop(ch <-chan int, d time.Duration) int {
	timer := time.NewTimer(d)
	defer timer.Stop()
	for {
		select {
		case v := <-ch:
			return v
		case <-timer.C:
			return 0
		}
	}
}

// WRONG: Continuing to select on a closed channel forever
func wrongClosedLoop(ch <-chan int) {
	for {
		select {
		case _, ok := <-ch:
			if !ok {
				continue // ch is always ready; this spins
			}
		}
	}
}

// CORRECT: Disable closed channels by assigning nil
func correctClosedLoop(ch1, ch2 <-chan int) {
	for ch1 != nil || ch2 != nil {
		select {
		case _, ok := <-ch1:
			if !ok {
				ch1 = nil
			}
		case _, ok := <-ch2:
			if !ok {
				ch2 = nil
			}
		}
	}
}

// WRONG: Assuming select chooses the first ready case
func wrongPriority(a, b <-chan int) int {
	select {
	case <-a:
		return 1
	case <-b:
		return 2
	}
}

// CORRECT: Handle randomized ready-case selection explicitly
func correctPriority(a, b <-chan int) int {
	var chosen int
	select {
	case <-a:
		chosen = 1
	case <-b:
		chosen = 2
	}
	return chosen
}

func tick() <-chan time.Time { return time.After(time.Millisecond) }
```

## Gotchas
- `select` blocks until at least one case can proceed unless it has a `default` case.
- A `default` case makes `select` non-blocking and returns immediately when no case is ready.
- When multiple cases are ready, Go chooses one pseudo-randomly; do not rely on source order for priority.
- Receiving from a closed channel always proceeds, so set the channel variable to `nil` after EOF.
- `time.After` is convenient, but repeated use in hot loops can waste timers; reuse `time.NewTimer` or `time.NewTicker`.
- Sends in `select` can block, so pair them with cancellation or a bounded buffer.
- Nil channels are safe in `select` and are a common way to disable cases.
- Closing an output channel from only one merging goroutine can panic; coordinate closure with `WaitGroup`.

## Related
- go/concurrency/patterns.md
- go/concurrency/sync-patterns.md
- go/stdlib/channels.md
- go/patterns/fan-in.md
- go/patterns/fan-out.md
