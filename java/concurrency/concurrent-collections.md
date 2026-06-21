---
id: "java-concurrency-concurrent-collections"
title: "Java Concurrent Collections"
language: "java"
category: "concurrency"
subcategory: "collections"
tags: ["java", "concurrency", "concurrent-collections", "ConcurrentHashMap", "CopyOnWriteArrayList", "BlockingQueue", "atomic"]
version: "17+"
retrieval_hint: "Java concurrent collections ConcurrentHashMap CopyOnWriteArrayList BlockingQueue ConcurrentLinkedQueue computeIfAbsent thread-safe iteration"
last_verified: "2026-06-20"
confidence: "medium"
---

# Java Concurrent Collections

## When to Use
- Sharing counters, caches, maps, sets, or queues between threads
- Avoiding `ConcurrentModificationException` during safe concurrent iteration
- Implementing producer-consumer pipelines with bounded `BlockingQueue` instances
- Maintaining rare-write, frequent-read lists such as subscriber registries
- Replacing coarse-grained `synchronizedMap` usage with finer-grained concurrent operations

## Standard Pattern

```java
import java.util.List;
import java.util.Map;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

public class ConcurrentCollectionsPatterns {

    private final ConcurrentMap<String, AtomicInteger> counters = new ConcurrentHashMap<>();
    private final ConcurrentLinkedQueue<String> events = new ConcurrentLinkedQueue<>();
    private final BlockingQueue<WorkItem> workQueue = new ArrayBlockingQueue<>(1000);
    private final CopyOnWriteArrayList<String> subscribers = new CopyOnWriteArrayList<>();

    public void recordEvent(String key) {
        counters.computeIfAbsent(key, ignored -> new AtomicInteger()).incrementAndGet();
        events.offer(key);
    }

    public Map<String, Integer> snapshotCounters() {
        return counters.entrySet().stream()
            .collect(Collectors.toUnmodifiableMap(
                Map.Entry::getKey,
                entry -> entry.getValue().get()
            ));
    }

    public boolean publish(String event) {
        boolean accepted = workQueue.offer(new WorkItem(event));
        if (accepted) {
            for (String subscriber : subscribers) {
                notifySubscriber(subscriber, event);
            }
        }
        return accepted;
    }

    public void subscribe(String subscriber) {
        subscribers.addIfAbsent(subscriber);
    }

    public WorkItem takeWork() throws InterruptedException {
        return workQueue.take();
    }

    private void notifySubscriber(String subscriber, String event) {
        System.out.println(subscriber + " received " + event);
    }

    public record WorkItem(String payload) {}
}
```

## Common Mistakes

```java
// WRONG: Manual check-then-act on a shared map
if (!counts.containsKey(key)) {
    counts.put(key, new AtomicInteger());
}
counts.get(key).incrementAndGet();

// CORRECT: Use ConcurrentHashMap atomic update methods
counts.computeIfAbsent(key, ignored -> new AtomicInteger()).incrementAndGet();

// WRONG: Using CopyOnWriteArrayList for a list that changes on every request
subscribers.add(newSubscriber);
subscribers.remove(oldSubscriber);

// CORRECT: Use CopyOnWriteArrayList only for rare writes and many reads
subscribers.addIfAbsent(newSubscriber);

// WRONG: Iterating a non-concurrent HashMap while other threads mutate it
for (String key : regularMap.keySet()) {
    process(key);
}

// CORRECT: Use a concurrent map or take a snapshot before iterating
for (String key : concurrentMap.keySet()) {
    process(key);
}

// WRONG: Busy polling a queue with immediate poll in a tight loop
while ((item = queue.poll()) != null) {
    process(item);
}

// CORRECT: Use blocking take for workers or timed poll for responsive loops
WorkItem item = queue.poll(100, TimeUnit.MILLISECONDS);
if (item != null) {
    process(item);
}
```

## Gotchas
- Concurrent collection iterators are weakly consistent and do not throw `ConcurrentModificationException`.
- Weakly consistent iteration does not mean the collection is an atomic snapshot.
- `compute`, `merge`, and `computeIfAbsent` functions should be short and should not block.
- `CopyOnWriteArrayList` copies the backing array on writes, so it is costly for frequent mutations.
- `BlockingQueue.offer` rejects work when capacity is full; `put` blocks until space is available.

## Related
- java/stdlib/collections.md
- java/stdlib/concurrency.md
- java/patterns/producer-consumer.md