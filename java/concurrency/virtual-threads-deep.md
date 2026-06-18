---
id: "java-concurrency-virtual-threads-deep"
title: "Java Virtual Threads — Deep Patterns and Best Practices (21+)"
language: "java"
category: "concurrency"
subcategory: "virtual-threads"
tags: ["java", "virtual-threads", "loom", "concurrency", "thread-per-request", "jdk21", "structured-concurrency"]
version: "21+"
retrieval_hint: "Java virtual threads structured concurrency thread-per-request executor loom pinned carrier"
last_verified: "2026-05-25"
confidence: "high"
---

# Java Virtual Threads — Deep Patterns and Best Practices (21+)

## When to Use
- IO-bound applications handling thousands of concurrent connections (HTTP servers, DB access)
- Replacing thread-per-request patterns where platform threads are exhausted
- Simplifying async code — write synchronous-style code without the thread pool overhead
- Microservices with high concurrency requirements (gateways, proxies, API servers)
- NOT for CPU-bound computation — virtual threads don't make CPU work faster

## Standard Pattern

```java
import java.time.Duration;
import java.util.List;
import java.util.concurrent.*;
import java.util.stream.IntStream;

public class VirtualThreadsPatterns {

    // --- Basic virtual thread creation ---
    void basicPatterns() {
        // Way 1: Thread.startVirtualThread(Runnable)
        var t = Thread.startVirtualThread(() -> {
            System.out.println("Running in virtual thread: " + Thread.currentThread());
        });

        // Way 2: Executors.newVirtualThreadPerTaskExecutor()
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            executor.submit(() -> handleRequest());
        }
        // Auto-closes: waits for all submitted tasks to complete

        // Way 3: Thread.ofVirtual()
        var factory = Thread.ofVirtual().name("request-").factory();
        var thread = factory.newThread(() -> handleRequest());
        thread.start();
    }

    void handleRequest() {
        // Blocking IO calls DON'T block the OS thread
        // The carrier thread is released to run other virtual threads
    }

    // --- StructuredTaskScope: structured concurrency (JDK 21+) ---
    record UserData(int userId, String name, String email) {}

    UserData fetchUserData(int userId) throws Exception {
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            // These run concurrently on virtual threads
            Subtask<String> nameTask = scope.fork(() -> fetchName(userId));
            Subtask<String> emailTask = scope.fork(() -> fetchEmail(userId));

            scope.join();             // Wait for all
            scope.throwIfFailed();    // Propagate first failure

            return new UserData(userId, nameTask.get(), emailTask.get());
        }
        // All forked tasks are automatically cancelled on scope exit
    }

    String fetchName(int userId) throws Exception {
        Thread.sleep(Duration.ofMillis(50)); // Simulates DB call
        return "User" + userId;
    }

    String fetchEmail(int userId) throws Exception {
        Thread.sleep(Duration.ofMillis(30)); // Simulates API call
        return "user" + userId + "@example.com";
    }

    // --- Thread pool replacement pattern ---
    // BEFORE (platform threads, limited to ~200-1000 concurrent):
    private final ExecutorService platformPool =
        Executors.newFixedThreadPool(200);

    void oldWay(List<Runnable> tasks) throws InterruptedException {
        var futures = tasks.stream()
            .map(task -> platformPool.submit(task))
            .toList();
        for (var f : futures) {
            try { f.get(); } catch (ExecutionException e) { /* handle */ }
        }
    }

    // AFTER (virtual threads, scales to 10,000+):
    void newWay(List<Runnable> tasks) throws InterruptedException {
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var futures = tasks.stream()
                .map(executor::submit)
                .toList();
            for (var f : futures) {
                try { f.get(); } catch (ExecutionException e) { /* handle */ }
            }
        }
    }

    // --- Semaphore usage (not thread pool) for rate limiting ---
    private final Semaphore dbConnections = new Semaphore(10);

    void accessDatabase() {
        try {
            dbConnections.acquire();  // Limits concurrency, NOT thread count
            // Use database connection
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } finally {
            dbConnections.release();
        }
    }
}
```

## Common Mistakes

```java
// WRONG: Pooling virtual threads — defeats the entire purpose
// Virtual threads are CHEAP. Pooling adds overhead with zero benefit.
ExecutorService bad = Executors.newFixedThreadPool(1000, Thread.ofVirtual().factory());
// Use newVirtualThreadPerTaskExecutor() instead — no pool!

// WRONG: Using synchronized blocks heavily (causes pinning)
// synchronized PINTS the virtual thread to a carrier thread
class BadSync {
    private final Object lock = new Object();

    void doWork() {
        synchronized (lock) {  // Pinning!
            // If this blocks (IO), the carrier thread is STUCK
            Thread.sleep(100);
        }
    }
}

// CORRECT: Use ReentrantLock instead of synchronized
import java.util.concurrent.locks.ReentrantLock;

class GoodLock {
    private final ReentrantLock lock = new ReentrantLock();

    void doWork() {
        lock.lock();
        try {
            Thread.sleep(100); // No pinning — carrier can do other work
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } finally {
            lock.unlock();
        }
    }
}

// WRONG: ThreadLocal misuse with virtual threads
// Virtual threads can outlive their purpose, causing ThreadLocal leaks
private static final ThreadLocal<String> requestId = new ThreadLocal<>();

void handleRequest() {
    requestId.set("req-123");  // May leak if thread is pooled (!)
    // With virtual threads: each request gets a NEW thread,
    // so ThreadLocal is CLEANED UP on thread exit... mostly.
    // BUT: InheritableThreadLocal STILL leaks!
}

// CORRECT: Use ScopeLocal (JDK 21+) instead of ThreadLocal
// ScopeLocal is designed for virtual threads and doesn't leak
public final static ScopeLocal<String> REQUEST_ID = ScopeLocal.named("requestId");

void handleRequest() {
    ScopeLocal.where(REQUEST_ID, "req-123", () -> {
        // Inside this scope, REQUEST_ID.get() returns "req-123"
        doWork();
    });
    // After scope exits, REQUEST_ID is automatically cleaned up
}

// WRONG: Catching InterruptedException and ignoring it
// Virtual threads use interruption for cancellation — swallowing InterruptedException
// prevents the carrier thread from being released.
try {
    Thread.sleep(1000);
} catch (InterruptedException e) {
    // Swallowed — virtual thread can't be cancelled
}

// CORRECT: Restore interrupt flag when you can't re-throw
try {
    Thread.sleep(1000);
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();  // Restore flag
    // Clean up and exit
    return;
}
```

## Gotchas
- **Pinning happens with synchronized, native frames, and JNI:** When a virtual thread enters a `synchronized` block and then blocks (e.g., IO), the carrier thread is "pinned" and cannot be reassigned. This limits scalability. Use `java.util.concurrent.locks.ReentrantLock` instead. Pinning also occurs during native method calls and JNI.
- **ThreadLocal memory is still freed:** Virtual threads are GC-eligible after they complete. `ThreadLocal` values are cleaned up when the virtual thread is garbage collected. However, `InheritableThreadLocal` can leak because it copies values to child threads. Avoid inheritable thread locals.
- **`Thread.stop()` and `Thread.suspend()` are still deadly:** These methods were deprecated for good reason. On virtual threads, they can leave carrier threads in inconsistent states. Never use them.
- **Debugging virtual threads requires JDK 21+ tools:** `jstack` doesn't show virtual thread stacks well. Use `jcmd <pid> Thread.vthread_print` or the JDK Flight Recorder for virtual thread profiling. IntelliJ 2023.2+ has improved virtual thread debugging support.
- **Custom thread pools interact poorly:** If you pass a virtual thread to a custom thread pool (e.g., `new ThreadPoolExecutor()`), the pool might cache the carrier thread, not the virtual thread. Always use `Executors.newVirtualThreadPerTaskExecutor()` or `StructuredTaskScope`.

## Related
- java/stdlib/records.md
- java/concurrency/structured-concurrency.md
