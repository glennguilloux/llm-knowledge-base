---
id: "java-concurrency-completable-future"
title: "Java CompletableFuture Composition"
language: "java"
category: "concurrency"
subcategory: "completable-future"
tags: ["java", "concurrency", "completable-future", "async", "then-compose", "then-apply", "exception-handling", "timeout"]
version: "17+"
retrieval_hint: "Java CompletableFuture composition thenApply thenCompose allOf exceptionally handle orTimeout supplyAsync async executor"
last_verified: "2026-06-20"
confidence: "medium"
---

# Java CompletableFuture Composition

## When to Use
- Chaining asynchronous operations without nested callbacks
- Transforming an async result with `thenApply` or flattening another async stage with `thenCompose`
- Running independent async stages in parallel and combining their results
- Adding timeouts, fallbacks, and structured exception handling to async pipelines
- Keeping blocking I/O off the shared `ForkJoinPool.commonPool()`

## Standard Pattern

```java
import java.util.List;
import java.util.Objects;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.TimeUnit;

public class CompletableFutureComposition {

    private final ExecutorService executor;

    public CompletableFutureComposition(ExecutorService executor) {
        this.executor = Objects.requireNonNull(executor, "executor");
    }

    public CompletableFuture<OrderSummary> loadOrderSummary(int userId) {
        CompletableFuture<User> userFuture = fetchUser(userId);
        CompletableFuture<List<Order>> ordersFuture =
            userFuture.thenCompose(user -> fetchOrders(user.id()));
        CompletableFuture<Double> balanceFuture =
            userFuture.thenCompose(user -> fetchBalance(user.id()));

        return CompletableFuture.allOf(ordersFuture, balanceFuture)
            .thenApply(ignored -> new OrderSummary(
                userFuture.join(),
                ordersFuture.join(),
                balanceFuture.join()
            ));
    }

    public CompletableFuture<String> loadOrderSummaryWithFallback(int userId) {
        return loadOrderSummary(userId)
            .orTimeout(5, TimeUnit.SECONDS)
            .handle((summary, error) -> {
                if (error == null) {
                    return summary.toString();
                }
                return "summary unavailable";
            });
    }

    private CompletableFuture<User> fetchUser(int userId) {
        return CompletableFuture.completedFuture(new User(userId, "Ada"));
    }

    private CompletableFuture<List<Order>> fetchOrders(int userId) {
        return CompletableFuture.supplyAsync(
            () -> List.of(new Order("order-1"), new Order("order-2")),
            executor
        );
    }

    private CompletableFuture<Double> fetchBalance(int userId) {
        return CompletableFuture.supplyAsync(() -> 125.50, executor);
    }

    private static void unwrap(CompletionException error) {
        Throwable cause = error.getCause();
        throw new IllegalStateException("Async stage failed", cause == null ? error : cause);
    }

    public record User(int id, String name) {}
    public record Order(String id) {}
    public record OrderSummary(User user, List<Order> orders, Double balance) {}
}
```

## Common Mistakes

```java
// WRONG: Blocking inside an async chain with join or get
CompletableFuture<String> bad = fetchUser(id)
    .thenApply(user -> fetchOrders(user.id()).join());

// CORRECT: Use thenCompose to flatten the nested async stage
CompletableFuture<List<Order>> good = fetchUser(id)
    .thenCompose(user -> fetchOrders(user.id()));

// WRONG: Silently replacing failures with null
CompletableFuture<String> lost = future
    .thenApply(String::toUpperCase)
    .exceptionally(error -> null);

// CORRECT: Log the failure and return a meaningful fallback
CompletableFuture<String> handled = future
    .thenApply(String::toUpperCase)
    .handle((value, error) -> {
        if (error == null) {
            return value;
        }
        return "fallback";
    });

// WRONG: Running blocking I/O on the common pool
CompletableFuture<String> badIo = CompletableFuture.supplyAsync(() -> httpClient.get(url));

// CORRECT: Use a dedicated executor for blocking or I/O-bound work
CompletableFuture<String> goodIo = CompletableFuture.supplyAsync(() -> httpClient.get(url), ioExecutor);

// WRONG: Calling allOf and then ignoring failed stages
CompletableFuture<Void> all = CompletableFuture.allOf(first, second);
all.thenRun(() -> readBoth());

// CORRECT: Check each stage after allOf or handle failures before combining
CompletableFuture<Result> combined = CompletableFuture.allOf(first, second)
    .thenApply(ignored -> new Result(first.join(), second.join()))
    .exceptionally(error -> Result.unavailable());
```

## Gotchas
- `thenApply` transforms a completed value; `thenCompose` chains another `CompletableFuture`.
- `CompletableFuture.join()` throws unchecked `CompletionException`; `Future.get()` throws checked exceptions.
- `allOf` completes exceptionally when any input stage completes exceptionally.
- `orTimeout` completes the stage exceptionally on timeout, so pair it with `exceptionally` or `handle`.
- The common pool is shared across the JVM; avoid blocking it with I/O or long CPU work.

## Related
- java/stdlib/completable-future.md
- java/stdlib/concurrency.md
- java/patterns/async-method-invocation.md