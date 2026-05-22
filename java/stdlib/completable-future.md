---
id: "java-stdlib-completable-future"
title: "CompletableFuture Advanced Patterns"
language: "java"
category: "concurrency"
tags: ["CompletableFuture", "async", "compose", "exception", "thenApply", "thenCompose"]
version: "17+"
retrieval_hint: "CompletableFuture async compose thenApply thenCompose exception handling supplyAsync"
last_verified: "2026-05-22"
confidence: "high"
---

# CompletableFuture Advanced Patterns

## When to Use
- Composing multiple async operations
- Non-blocking I/O with timeout and fallback
- Parallel execution with result aggregation
- Replacing callback hell with fluent async chains

## Standard Pattern

```java
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.List;

public class AsyncPatterns {

    private static final ExecutorService executor = Executors.newFixedThreadPool(10);

    // --- Basic async operation ---
    public static CompletableFuture<String> fetchData(String url) {
        return CompletableFuture.supplyAsync(() -> {
            // Simulate network call
            return "data from " + url;
        }, executor);
    }

    // --- Transform result ---
    public static CompletableFuture<Integer> processData(String url) {
        return fetchData(url)
            .thenApply(data -> data.length())  // Transform
            .thenApply(len -> len * 2);        // Chain
    }

    // --- Compose async operations ---
    public static CompletableFuture<User> getUserWithOrders(int userId) {
        return fetchUser(userId)
            .thenCompose(user -> fetchOrders(user.id())  // FlatMap
                .thenApply(orders -> user.withOrders(orders)));
    }

    // --- Parallel execution ---
    public static CompletableFuture<Dashboard> loadDashboard(int userId) {
        CompletableFuture<User> userFuture = fetchUser(userId);
        CompletableFuture<List<Order>> ordersFuture = fetchOrders(userId);
        CompletableFuture<List<Notification>> notifsFuture = fetchNotifications(userId);

        return CompletableFuture.allOf(userFuture, ordersFuture, notifsFuture)
            .thenApply(v -> new Dashboard(
                userFuture.join(),
                ordersFuture.join(),
                notifsFuture.join()
            ));
    }

    // --- Timeout and fallback ---
    public static CompletableFuture<String> fetchWithFallback(String url) {
        return fetchData(url)
            .orTimeout(5, java.util.concurrent.TimeUnit.SECONDS)  // Java 9+
            .exceptionally(ex -> "fallback data");  // Fallback on error
    }

    // --- Error handling ---
    public static CompletableFuture<String> fetchWithRecovery(String url) {
        return fetchData(url)
            .handle((result, ex) -> {
                if (ex != null) {
                    return "error: " + ex.getMessage();
                }
                return result;
            });
    }

    // --- Race (first wins) ---
    public static CompletableFuture<String> fetchFastest(String url1, String url2) {
        CompletableFuture<String> f1 = fetchData(url1);
        CompletableFuture<String> f2 = fetchData(url2);
        return f1.applyToEither(f2, data -> data);
    }
}
```

## Common Mistakes

```java
// WRONG: Blocking in async chain
CompletableFuture.supplyAsync(() -> {
    return blockingCall();  // Blocks the common pool thread!
});

// CORRECT: Use dedicated executor for blocking work
CompletableFuture.supplyAsync(() -> blockingCall(), ioExecutor);

// WRONG: Swallowing exceptions
future.thenApply(data -> process(data))
      .exceptionally(ex -> null);  // Exception lost!

// CORRECT: Log and handle
future.thenApply(data -> process(data))
      .exceptionally(ex -> {
          log.error("Failed", ex);
          return fallback;
      });

// WRONG: Not using thenCompose for async chaining
future.thenApply(data -> fetchMore(data).join());  // Blocks!

// CORRECT: Use thenCompose (flatMap)
future.thenCompose(data -> fetchMore(data));

// WRONG: Using common pool for blocking I/O
CompletableFuture.supplyAsync(() -> httpClient.get(url));  // Blocks ForkJoinPool!

// CORRECT: Use dedicated executor
CompletableFuture.supplyAsync(() -> httpClient.get(url), ioExecutor);
```

## Gotchas
- `thenApply` transforms synchronously; `thenCompose` chains async operations (flatMap)
- `ForkJoinPool.commonPool()` is shared — never block it with I/O
- `allOf()` returns `CompletableFuture<Void>` — use `.join()` to get individual results
- `orTimeout()` (Java 9+) throws `TimeoutException` — use `exceptionally()` for fallback
- `handle()` receives both result and exception — useful for logging or cleanup
- `applyToEither()` returns the first completed result — useful for redundancy
- `join()` throws unchecked `CompletionException`; `get()` throws checked `ExecutionException`

## Related
- java/stdlib/concurrency.md
- java/stdlib/exception-handling.md
