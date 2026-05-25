---
id: "antipatterns-concurrency"
title: "Concurrency Anti-Patterns: Race Conditions, Deadlocks, and Goroutine Leaks"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "concurrency", "race-conditions", "deadlocks", "goroutine-leaks", "thread-starvation", "shared-mutable-state"]
version: "n/a"
retrieval_hint: "concurrency antipatterns race conditions deadlocks not using locks shared mutable state goroutine leaks thread starvation"
last_verified: "2026-05-24"
confidence: "high"
---

# Concurrency Anti-Patterns: Race Conditions, Deadlocks, and Goroutine Leaks

## When to Use
- Writing concurrent or parallel code
- Reviewing code for thread safety
- Debugging race conditions and deadlocks
- Training LLMs to write safe concurrent code

## Standard Pattern

```python
# === Python Examples ===

# WRONG: Race condition (shared mutable state without lock)
import threading

counter = 0  # Shared mutable state!

def increment():
    global counter
    for _ in range(100000):
        counter += 1  # NOT atomic! Race condition!

threads = [threading.Thread(target=increment) for _ in range(10)]
for t in threads: t.start()
for t in threads: t.join()
print(counter)  # Expected: 1000000, Actual: varies!

# CORRECT: Use Lock for thread safety
import threading

counter = 0
lock = threading.Lock()

def increment():
    global counter
    for _ in range(100000):
        with lock:
            counter += 1

# WRONG: Deadlock (circular lock acquisition)
lock_a = threading.Lock()
lock_b = threading.Lock()

def thread_1():
    with lock_a:
        time.sleep(0.1)
        with lock_b:  # Waits for lock_b held by thread_2
            pass

def thread_2():
    with lock_b:
        time.sleep(0.1)
        with lock_a:  # Waits for lock_a held by thread_1
            pass
# DEADLOCK! Both threads wait forever.

# CORRECT: Always acquire locks in the same order
def thread_1():
    with lock_a:
        with lock_b:
            pass

def thread_2():
    with lock_a:  # Same order!
        with lock_b:
            pass

# === Go Examples ===

# WRONG: Goroutine leak
# go func() {
#     for {
#         select {
//         case <-ch:
//             process()
//         }
//     }
// }()
// Goroutine runs forever even when no longer needed!

# CORRECT: Use context for cancellation
# ctx, cancel := context.WithCancel(context.Background())
# go func() {
#     for {
#         select {
//         case <-ctx.Done():
//             return  // Clean exit
//         case <-ch:
//             process()
//         }
//     }
# }()
# cancel()  // Signal goroutine to stop

# WRONG: Race condition in Go
# var counter int
# for i := 0; i < 10; i++ {
#     go func() {
#         counter++  // Race condition!
#     }()
# }

# CORRECT: Use sync.Mutex or sync/atomic
# var counter int64
# var mu sync.Mutex
# for i := 0; i < 10; i++ {
#     go func() {
#         mu.Lock()
#         counter++
#         mu.Unlock()
#     }()
# }
# Or: atomic.AddInt64(&counter, 1)

# === Java Examples ===

# WRONG: Not synchronizing shared state
# private int counter = 0;
# public void increment() { counter++; }  // Not thread-safe!

# CORRECT: Use synchronized or AtomicInteger
# private AtomicInteger counter = new AtomicInteger(0);
# public void increment() { counter.incrementAndGet(); }

# WRONG: Holding lock while doing I/O
# synchronized(lock) {
#     // Database query while holding lock — blocks all other threads!
#     db.query("SELECT ...");
# }

# CORRECT: Minimize lock scope
# Result result;
# synchronized(lock) {
#     result = cache.get(key);
# }
# if (result == null) {
#     result = db.query("SELECT ...");  // I/O outside lock
#     synchronized(lock) {
#         cache.put(key, result);
#     }
# }
```

## Common Mistakes
- Race conditions — shared mutable state without locks causes non-deterministic bugs
- Deadlocks — circular lock acquisition (thread A waits for lock B, thread B waits for lock A)
- Goroutine leaks — goroutines that never terminate accumulate and exhaust memory
- Thread starvation — holding locks too long blocks other threads
- Not using atomic operations — simple counters need atomic increment, not plain ++
- Ignoring happens-before — changes in one thread may not be visible to another without synchronization

## Gotchas
- Race conditions are non-deterministic. Tests may pass 999 times and fail once.
- Deadlocks can be prevented by always acquiring locks in a consistent global order.
- Goroutine leaks accumulate over time and cause memory exhaustion.
- `sync/atomic` operations are faster than mutexes for simple counters.
- In Python, the GIL prevents true parallelism for CPU-bound work. Use `multiprocessing`.
- In Go, use `go run -race` to detect race conditions at runtime.
- Thread starvation occurs when one thread holds a lock for too long.
- Immutable data is inherently thread-safe. Prefer immutability.
- Channel-based communication (Go) is often safer than shared memory.

## Related
- anti-patterns/testing-antipatterns.md
- anti-patterns/error-handling-antipatterns.md
- anti-patterns/logging-antipatterns.md
- kotlin/stdlib/coroutines.md
