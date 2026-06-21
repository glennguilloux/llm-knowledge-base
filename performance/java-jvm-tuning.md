---
id: "performance-java-jvm-tuning"
title: "Java JVM Tuning"
language: "java"
category: "performance"
tags: ["java", "jvm", "heap", "gc", "g1gc", "performance", "tuning"]
version: "17+"
retrieval_hint: "Java JVM tuning heap garbage collection GC G1GC flags memory performance throughput latency diagnostics"
last_verified: "2026-06-20"
confidence: "medium"
---

# Java JVM Tuning

## When to Use
- Diagnosing Java service latency, throughput, or memory-pressure symptoms
- Setting sane JVM flags for long-running server applications
- Choosing garbage collection diagnostics before changing heap size
- Comparing relative effects of JVM options in a controlled environment

## Standard Pattern

```java
// === Production JVM options: start conservative and measure ===
// java
//   -XX:+UseG1GC
//   -Xms512m
//   -Xmx512m
//   -XX:MaxGCPauseMillis=200
//   -XX:+HeapDumpOnOutOfMemoryError
//   -XX:HeapDumpPath=/var/app/heapdumps
//   -Xlog:gc*:file=/var/app/logs/gc.log:time,uptime,level,tags
//   -jar app.jar
```

```java
// === Runtime diagnostics with ManagementFactory ===
import java.lang.management.GarbageCollectorMXBean;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.MemoryUsage;

public final class JvmDiagnostics {
    public static void printJvmSnapshot() {
        MemoryMXBean memory = ManagementFactory.getMemoryMXBean();
        MemoryUsage heap = memory.getHeapMemoryUsage();

        System.out.printf(
            "heap-used=%d heap-committed=%d heap-max=%d%n",
            heap.getUsed(),
            heap.getCommitted(),
            heap.getMax()
        );

        for (GarbageCollectorMXBean gc : ManagementFactory.getGarbageCollectorMXBeans()) {
            System.out.printf(
                "gc=%s collection-count=%s collection-time=%s%n",
                gc.getName(),
                gc.getCollectionCount(),
                gc.getCollectionTime()
            );
        }
    }
}
```

```java
// === Controlled benchmark harness shape ===
public final class TuningHarness {
    public static void main(String[] args) {
        warmUp();
        long start = System.nanoTime();
        runRepresentativeWorkload();
        long elapsed = System.nanoTime() - start;
        System.out.println("elapsed-nanos=" + elapsed);
    }

    private static void warmUp() {
        for (int i = 0; i < 1000; i++) {
            runRepresentativeWorkload();
        }
    }

    private static void runRepresentativeWorkload() {
        // Exercise the same request mix, data size, and dependencies as production.
    }
}
```

## Common Mistakes

```java
// WRONG: Increasing heap size without checking GC behavior
// java -Xmx8g -jar app.jar

// CORRECT: Pair heap sizing with GC logging and memory snapshots
// java -Xms512m -Xmx512m -XX:+UseG1GC -Xlog:gc*:file=gc.log app.jar
```

```java
// WRONG: Setting min and max heap far apart for latency-sensitive services
// java -Xms256m -Xmx8g -jar app.jar

// CORRECT: Use equal min and max heap when predictable memory behavior matters
// java -Xms512m -Xmx512m -XX:+UseG1GC -jar app.jar
```

```java
// WRONG: Tuning JVM flags from a synthetic microbenchmark only
// Run one tiny loop and copy the fastest flags to production

// CORRECT: Tune with representative workload, warm-up, and production-like data
JvmDiagnostics.printJvmSnapshot();
runRepresentativeWorkload();
```

```java
// WRONG: Treating OutOfMemoryError as only a heap-size problem
try {
    processLargePayload();
} catch (OutOfMemoryError error) {
    System.exit(1);
}

// CORRECT: Capture heap evidence and inspect retention causes
// java -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/var/app/heapdumps
// Then analyze heap dumps and allocation sites before changing flags
```

## Gotchas
- Heap size, garbage collector choice, pause targets, and allocation rate interact; change one setting at a time
- Equal `-Xms` and `-Xmx` can reduce resizing churn but requires enough container memory headroom
- GC logging is essential evidence; tuning without logs is usually guesswork
- Container limits matter: configure the JVM so it understands available memory in orchestrated environments
- Native memory, direct buffers, thread stacks, and heap are separate consumers of process memory
- A smaller pause target can increase total GC work; verify latency and throughput together

## Related
- performance/database-optimization.md
- performance/memory-patterns.md
- performance/connection-pooling.md
