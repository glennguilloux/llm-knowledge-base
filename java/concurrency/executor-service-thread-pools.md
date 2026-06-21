---
id: "java-concurrency-executor-service"
title: "Java ExecutorService Thread Pools"
language: "java"
category: "concurrency"
subcategory: "executor-service"
tags: ["java", "concurrency", "executor-service", "thread-pool", "future", "shutdown", "thread-factory"]
version: "17+"
retrieval_hint: "Java ExecutorService thread pool lifecycle shutdown newFixedThreadPool ThreadPoolExecutor Future invokeAll awaitTermination saturation policy"
last_verified: "2026-06-20"
confidence: "medium"
---

# Java ExecutorService Thread Pools

## When to Use
- Running bounded parallel work such as request handling, batch jobs, or CPU-bound task sets
- Submitting `Callable` or `Runnable` work and collecting `Future` results with timeouts
- Controlling resource usage with a fixed worker count, bounded queue, and explicit shutdown
- Adding back pressure when more work arrives than the pool can process immediately
- Replacing ad hoc `new Thread(...)` usage where lifecycle management matters

## Standard Pattern

```java
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.Callable;
import java.util.concurrent.CancellationException;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;

public class ExecutorServiceThreadPools {

    private final ExecutorService executor;

    public ExecutorServiceThreadPools(int workerCount) {
        if (workerCount <= 0) {
            throw new IllegalArgumentException("workerCount must be positive");
        }

        BlockingQueue<Runnable> workQueue = new ArrayBlockingQueue<>(workerCount * 4);
        ThreadFactory threadFactory = new NamedThreadFactory("worker");
        this.executor = new ThreadPoolExecutor(
            workerCount,
            workerCount,
            0L,
            TimeUnit.MILLISECONDS,
            workQueue,
            threadFactory,
            new ThreadPoolExecutor.CallerRunsPolicy()
        );
    }

    public List<String> normalizeAll(List<String> values) throws InterruptedException {
        List<Future<String>> futures = new ArrayList<>(values.size());

        for (String value : values) {
            try {
                futures.add(executor.submit(() -> normalize(value)));
            } catch (RejectedExecutionException e) {
                throw new IllegalStateException("Executor rejected task", e);
            }
        }

        List<String> results = new ArrayList<>(values.size());
        for (Future<String> future : futures) {
            try {
                results.add(future.get(5, TimeUnit.SECONDS));
            } catch (TimeoutException e) {
                future.cancel(true);
                throw new IllegalStateException("Task timed out", e);
            } catch (ExecutionException e) {
                throw new IllegalStateException("Task failed", e.getCause());
            } catch (CancellationException e) {
                throw new IllegalStateException("Task was cancelled", e);
            }
        }

        return results;
    }

    private String normalize(String value) {
        return value.toUpperCase(Locale.ROOT);
    }

    public void shutdown() throws InterruptedException {
        executor.shutdown();
        if (!executor.awaitTermination(10, TimeUnit.SECONDS)) {
            executor.shutdownNow();
            if (!executor.awaitTermination(5, TimeUnit.SECONDS)) {
                throw new IllegalStateException("Executor did not terminate");
            }
        }
    }

    private static final class NamedThreadFactory implements ThreadFactory {
        private final String prefix;
        private final AtomicInteger index = new AtomicInteger(1);

        private NamedThreadFactory(String prefix) {
            this.prefix = prefix;
        }

        @Override
        public Thread newThread(Runnable task) {
            Thread thread = new Thread(task, prefix + "-" + index.getAndIncrement());
            thread.setDaemon(false);
            return thread;
        }
    }
}
```

## Common Mistakes

```java
// WRONG: Using an unbounded cached pool for uncontrolled input
ExecutorService unsafe = Executors.newCachedThreadPool();
// A burst of requests can create thousands of threads and exhaust memory.

// CORRECT: Use a bounded pool and queue for predictable resource usage
ExecutorService safe = new ThreadPoolExecutor(
    8,
    8,
    0L,
    TimeUnit.MILLISECONDS,
    new ArrayBlockingQueue<>(100),
    new ThreadPoolExecutor.CallerRunsPolicy()
);

// WRONG: Calling shutdownNow immediately after submitting work
executor.submit(() -> saveOrder());
executor.shutdownNow();
// Tasks may never run, and in-flight work can be interrupted abruptly.

// CORRECT: Stop accepting new work, wait, then force cancellation only if needed
executor.shutdown();
if (!executor.awaitTermination(10, TimeUnit.SECONDS)) {
    executor.shutdownNow();
}

// WRONG: Swallowing InterruptedException and continuing as if cancellation did not happen
try {
    future.get();
} catch (InterruptedException e) {
    // Lost interrupt flag
}

// CORRECT: Restore the interrupt flag and stop the current operation
try {
    future.get();
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();
    throw new IllegalStateException("Interrupted while waiting for task", e);
}

// WRONG: Blocking forever on Future.get without a timeout
String result = future.get();

// CORRECT: Use a timeout and cancel the task if it cannot finish promptly
try {
    String result = future.get(5, TimeUnit.SECONDS);
} catch (TimeoutException e) {
    future.cancel(true);
}
```

## Gotchas
- `Executors.newFixedThreadPool(n)` uses an unbounded `LinkedBlockingQueue`, which can hide overload until memory is exhausted.
- `CallerRunsPolicy` provides back pressure by running rejected work on the caller, but it can slow down the producer.
- Always restore the interrupt flag after catching `InterruptedException` unless you rethrow it.
- A timed `Future.get` can still leave work running unless the `Future` is cancelled.
- Named thread factories make logs, thread dumps, and debugging much easier.

## Related
- java/stdlib/concurrency.md
- java/concurrency/virtual-threads-deep.md
- java/patterns/producer-consumer.md