---
id: "java-stdlib-concurrency"
title: "Java Concurrency with ExecutorService"
language: "java"
category: "stdlib"
subcategory: "concurrency"
tags: ["concurrency", "executor", "future", "completable-future", "thread"]
version: "17+"
retrieval_hint: "Java concurrency executor future thread pool async"
last_verified: "2026-05-22"
confidence: "high"
---

# Java Concurrency with ExecutorService

## When to Use
- Running tasks in parallel
- Managing thread pools
- Asynchronous computation
- Timeout handling

## Standard Pattern

```java
import java.util.concurrent.*;
import java.util.List;
import java.util.ArrayList;

// Create thread pool
ExecutorService executor = Executors.newFixedThreadPool(4);

// Submit Callable (returns value)
Future<String> future = executor.submit(() -> {
    Thread.sleep(1000);
    return "Result";
});

String result = future.get();  // Blocks until complete
String resultWithTimeout = future.get(5, TimeUnit.SECONDS);  // With timeout

// Submit Runnable (no return value)
executor.submit(() -> System.out.println("Running"));

// CompletableFuture (Java 8+)
CompletableFuture<String> cf = CompletableFuture.supplyAsync(() -> {
    return "Hello";
}, executor);

cf.thenApply(result -> result + " World")
   .thenAccept(System.out::println);

// Chain multiple async operations
CompletableFuture<String> combined = CompletableFuture
    .supplyAsync(() -> fetchData(), executor)
    .thenApply(data -> process(data))
    .thenCompose(data -> saveAsync(data))
    .exceptionally(ex -> "Fallback value");

// Invoke all tasks and wait
List<Callable<String>> tasks = List.of(
    () -> fetchFrom("service1"),
    () -> fetchFrom("service2"),
    () -> fetchFrom("service3")
);

List<Future<String>> futures = executor.invokeAll(tasks);
List<String> results = new ArrayList<>();
for (Future<String> f : futures) {
    results.add(f.get());
}

// Shutdown
executor.shutdown();
if (!executor.awaitTermination(10, TimeUnit.SECONDS)) {
    executor.shutdownNow();
}
```

## Common Mistakes

```java
// WRONG: Not shutting down executor
ExecutorService executor = Executors.newFixedThreadPool(4);
executor.submit(() -> work());
// App never exits!

// CORRECT: Always shutdown
executor.shutdown();

// WRONG: Using get() without timeout
String result = future.get();  // Blocks forever if task hangs

// CORRECT: Use timeout
String result = future.get(5, TimeUnit.SECONDS);

// WRONG: Swallowing exceptions in CompletableFuture
cf.exceptionally(ex -> null);  // Silently loses error!

// CORRECT: Handle exceptions properly
cf.exceptionally(ex -> {
    log.error("Failed", ex);
    return fallback;
});
```

## Gotchas
- `Executors.newFixedThreadPool(n)` creates n threads
- `future.get()` blocks the calling thread
- `CompletableFuture.supplyAsync()` uses ForkJoinPool by default
- Always call `executor.shutdown()` to release resources
- `invokeAll()` waits for all tasks; `invokeAny()` returns first completed
- Use `CompletableFuture.allOf()` to wait for multiple futures
- `Thread.sleep()` blocks the current thread

## Related
- java/stdlib/streams.md
- java/spring/boot-basics.md
