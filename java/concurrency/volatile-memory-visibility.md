---
id: "java-concurrency-volatile-visibility"
title: "Java Volatile and Memory Visibility"
language: "java"
category: "concurrency"
subcategory: "volatile"
tags: ["java", "concurrency", "volatile", "memory-visibility", "happens-before", "safe-publication", "thread-safe"]
version: "17+"
retrieval_hint: "Java volatile memory visibility happens-before safe publication shared flag thread-safe immutable reference"
last_verified: "2026-06-20"
confidence: "medium"
---

# Java Volatile and Memory Visibility

## When to Use
- Publishing a simple shared flag such as `running`, `cancelled`, or `shutdownRequested`
- Reading a shared reference that is replaced as an immutable value
- Making writes visible to other threads without full mutual exclusion
- Supporting safe publication of configuration snapshots or status objects
- Implementing simple state checks where each operation is a single read or write

## Standard Pattern

```java
import java.time.Duration;

public class VolatileVisibilityPatterns {

    private volatile boolean running;
    private volatile Configuration configuration;

    public void start() {
        running = true;
    }

    public void stop() {
        running = false;
    }

    public boolean isRunning() {
        return running;
    }

    public void reloadConfiguration(Configuration next) {
        configuration = next;
    }

    public Configuration currentConfiguration() {
        return configuration;
    }

    public void processWhileRunning(Runnable work) {
        while (running) {
            work.run();
        }
    }

    public record Configuration(String endpoint, Duration timeout) {}
}
```

## Common Mistakes

```java
// WRONG: Using a plain boolean flag for cross-thread shutdown
private boolean running = true;

public void stop() {
    running = false;
}

// CORRECT: Use volatile for a simple cross-thread flag
private volatile boolean running = true;

// WRONG: Using volatile for a compound read-modify-write operation
private volatile int count;
count++;

// CORRECT: Use AtomicInteger or synchronize compound updates
AtomicInteger count = new AtomicInteger();
count.incrementAndGet();

// WRONG: Publishing a mutable object through a volatile reference
private volatile MutableConfig config;
config.setEndpoint("new-host");

// CORRECT: Publish immutable snapshots instead
private volatile ConfigSnapshot config;
config = new ConfigSnapshot("new-host");

// WRONG: Double-checked locking without a volatile instance field
if (helper == null) {
    synchronized (this) {
        if (helper == null) {
            helper = new Helper();
        }
    }
}

// CORRECT: Use volatile for the shared reference in double-checked locking
private volatile Helper helper;
```

## Gotchas
- `volatile` guarantees visibility and ordering for reads and writes of the variable itself.
- `volatile` does not make compound actions atomic; use locks, CAS, or atomic classes.
- A volatile reference does not make the referenced object thread-safe.
- Immutable records and final fields are often safer for publishing shared configuration.
- Overusing volatile can reduce optimization opportunities without providing full synchronization.

## Related
- java/stdlib/concurrency.md
- java/concurrency/virtual-threads-deep.md
- java/patterns/double-checked-locking.md