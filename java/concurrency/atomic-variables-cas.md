---
id: "java-concurrency-atomic-variables"
title: "Java Atomic Variables and CAS"
language: "java"
category: "concurrency"
subcategory: "atomic-variables"
tags: ["java", "concurrency", "atomic", "cas", "compare-and-set", "AtomicInteger", "AtomicReference", "LongAdder"]
version: "17+"
retrieval_hint: "Java atomic variables CAS compareAndSet AtomicInteger AtomicReference optimistic locking LongAdder non-blocking synchronization"
last_verified: "2026-06-20"
confidence: "medium"
---

# Java Atomic Variables and CAS

## When to Use
- Implementing lock-free counters, ids, flags, or single-value state transitions
- Updating one shared value with compare-and-set instead of a full lock
- Avoiding lost updates from read-modify-write sequences such as counters
- Building optimistic concurrency checks for small state machines
- Reducing contention where short CAS loops are faster than blocking locks

## Standard Pattern

```java
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.atomic.LongAdder;

public class AtomicVariablesCas {

    private final AtomicInteger nextId = new AtomicInteger(1);
    private final AtomicReference<State> state = new AtomicReference<>(State.IDLE);
    private final LongAdder requestCounter = new LongAdder();

    public int allocateId() {
        return nextId.getAndIncrement();
    }

    public boolean transition(State expected, State next) {
        return state.compareAndSet(expected, next);
    }

    public void recordRequest() {
        requestCounter.increment();
    }

    public long requestCount() {
        return requestCounter.sum();
    }

    public void updateMaxObserved(AtomicInteger max, int observed) {
        while (true) {
            int current = max.get();
            if (observed <= current) {
                return;
            }
            if (max.compareAndSet(current, observed)) {
                return;
            }
        }
    }

    public enum State {
        IDLE,
        RUNNING,
        STOPPED
    }
}
```

## Common Mistakes

```java
// WRONG: Read-modify-write on shared mutable state without synchronization
if (state.get() == State.IDLE) {
    state.set(State.RUNNING);
}

// CORRECT: Use compareAndSet for an atomic transition
state.compareAndSet(State.IDLE, State.RUNNING);

// WRONG: Using plain int increment from multiple threads
sharedCount++;

// CORRECT: Use AtomicInteger or LongAdder for shared counters
AtomicInteger count = new AtomicInteger();
count.incrementAndGet();

// WRONG: Mutating the object stored inside AtomicReference without CAS
User user = ref.get();
user.setName("Ada");

// CORRECT: Replace immutable values with CAS
User next = user.withName("Ada");
ref.compareAndSet(user, next);

// WRONG: Doing blocking work inside a CAS retry loop
while (true) {
    Snapshot current = snapshot.get();
    Snapshot next = loadFromDisk(current);
    if (snapshot.compareAndSet(current, next)) {
        break;
    }
}

// CORRECT: Keep CAS loops short and move blocking work outside the retry path
Snapshot base = snapshot.get();
Snapshot next = loadFromDisk(base);
while (!snapshot.compareAndSet(base, next)) {
    base = snapshot.get();
    next = loadFromDisk(base);
}
```

## Gotchas
- Atomic variables provide volatile reads and writes, but they do not make multi-step invariants atomic.
- CAS loops can spin under high contention; `LongAdder` is often better for high-rate counters.
- `AtomicReference` does not make the referenced object thread-safe; prefer immutable records for payloads.
- ABA can matter when a value changes away and back between reads; use stamps or locks when that matters.
- Blocking inside CAS loops increases contention and can waste CPU.

## Related
- java/stdlib/concurrency.md
- java/patterns/optimistic-offline-lock.md
- java/patterns/double-checked-locking.md