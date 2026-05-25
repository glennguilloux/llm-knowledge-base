---
id: "performance-memory-patterns"
title: "Memory Leak Patterns Across Languages"
language: "multi"
category: "performance"
tags: ["memory", "leaks", "profiling", "gc", "goroutine-leak", "closure-reference", "performance"]
version: "n/a"
retrieval_hint: "memory leak patterns profiling garbage collection closure reference goroutine leak OOM heap tuning"
last_verified: "2026-05-24"
confidence: "high"
---

# Memory Leak Patterns Across Languages

## When to Use
- Debugging growing memory usage in production
- Profiling applications with unbounded memory growth
- Understanding GC behavior in different languages
- Preventing memory leaks in long-running processes

## Standard Pattern

```python
# === Python: Common Leak Patterns ===

import weakref
import gc
import tracemalloc

# CORRECT: Start memory profiling
tracemalloc.start()
# ... run your code ...
snapshot = tracemalloc.take_snapshot()
for stat in snapshot.statistics("lineno")[:10]:
    print(stat)

# Pattern 1: Circular references with __del__
# WRONG: Circular reference prevents garbage collection
class Node:
    def __init__(self):
        self.parent = None
        self.children = []

    def __del__(self):
        pass  # __del__ prevents GC from breaking cycles in CPython < 3.4

# CORRECT: Use weakref for back-references
class Node:
    def __init__(self):
        self._parent: weakref.ref | None = None
        self.children: list["Node"] = []

    @property
    def parent(self):
        return self._parent() if self._parent else None

    @parent.setter
    def parent(self, value):
        self._parent = weakref.ref(value) if value else None

# Pattern 2: Global caches growing unbounded
# WRONG: Cache grows forever
_cache: dict[str, bytes] = {}

def get_data(key: str) -> bytes:
    if key not in _cache:
        _cache[key] = fetch_from_db(key)  # Never evicted!
    return _cache[key]

# CORRECT: Bounded cache with LRU eviction
from functools import lru_cache

@lru_cache(maxsize=1024)
def get_data(key: str) -> bytes:
    return fetch_from_db(key)

# Pattern 3: Closures holding references
# WRONG: Closure captures entire large_object
def create_handler(large_object: dict):
    def handler():
        return large_object["key"]  # Keeps entire dict alive
    return handler

# CORRECT: Capture only what's needed
def create_handler(large_object: dict):
    needed_value = large_object["key"]  # Extract before closure
    def handler():
        return needed_value
    return handler

# CORRECT: Force garbage collection when needed
gc.collect()  # Usually not needed — GC runs automatically
```

```java
// === Java: Heap Management ===

import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;

// CORRECT: Monitor heap usage
MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
long used = memoryBean.getHeapMemoryUsage().getUsed();
long max = memoryBean.getHeapMemoryUsage().getMax();
double usagePercent = (double) used / max * 100;

// CORRECT: JVM tuning flags for production
// -Xms512m -Xmx2g              // Min/max heap size
// -XX:+UseG1GC                  // G1 garbage collector (default in Java 11+)
// -XX:MaxGCPauseMillis=200      // Target max pause time
// -XX:+HeapDumpOnOutOfMemoryError  // Dump heap on OOM for analysis
// -XX:HeapDumpPath=/tmp/heap.hprof

// Pattern 1: Unclosed resources
// WRONG: ResultSet not closed (memory leak in connection pool)
public List<User> getUsers() throws SQLException {
    Statement stmt = conn.createStatement();
    ResultSet rs = stmt.executeQuery("SELECT * FROM users");
    // If exception thrown here, rs and stmt are never closed!
    List<User> users = mapUsers(rs);
    rs.close();
    stmt.close();
    return users;
}

// CORRECT: Try-with-resources
public List<User> getUsers() throws SQLException {
    try (Statement stmt = conn.createStatement();
         ResultSet rs = stmt.executeQuery("SELECT * FROM users")) {
        return mapUsers(rs);  // Auto-closed even on exception
    }
}

// Pattern 2: Static collections growing forever
// WRONG: Static list never cleared
public class EventLog {
    private static final List<Event> events = new ArrayList<>();
    public static void log(Event e) { events.add(e); }  // Grows forever!
}

// CORRECT: Bounded collection
public class EventLog {
    private static final int MAX_EVENTS = 10_000;
    private static final ArrayDeque<Event> events = new ArrayDeque<>(MAX_EVENTS);
    public static synchronized void log(Event e) {
        if (events.size() >= MAX_EVENTS) events.pollFirst();
        events.addLast(e);
    }
}
```

```go
// === Go: Goroutine Leaks ===

import "runtime"

// CORRECT: Monitor goroutine count
func monitorGoroutines() {
    ticker := time.NewTicker(10 * time.Second)
    for range ticker.C {
        fmt.Printf("Goroutines: %d\n", runtime.NumGoroutine())
    }
}

// Pattern 1: Goroutine waiting forever on channel
// WRONG: Goroutine blocks forever if no one reads from done
func process(done chan<- struct{}) {
    go func() {
        doWork()
        done <- struct{}{}  // Blocks forever if no reader!
    }()
}

// CORRECT: Use context for cancellation
func process(ctx context.Context) error {
    errCh := make(chan error, 1)  // Buffered — goroutine can exit
    go func() {
        errCh <- doWork()
    }()
    select {
    case err := <-errCh:
        return err
    case <-ctx.Done():
        return ctx.Err()
    }
}

// Pattern 2: HTTP response body not closed
// WRONG: Body never closed — connection leaks
resp, err := http.Get(url)
if err != nil { return err }
// Missing: defer resp.Body.Close()
data, _ := io.ReadAll(resp.Body)

// CORRECT: Always close response body
resp, err := http.Get(url)
if err != nil { return err }
defer resp.Body.Close()
data, err := io.ReadAll(resp.Body)
```

```typescript
// === TypeScript: Closure and Event Listener Leaks ===

// Pattern 1: Event listeners never removed
// WRONG: Listener added on every render
function Component({ id }: { id: string }) {
    useEffect(() => {
        window.addEventListener("resize", handler);  // Never removed!
    });
}

// CORRECT: Clean up in useEffect return
function Component({ id }: { id: string }) {
    useEffect(() => {
        const handler = () => { /* ... */ };
        window.addEventListener("resize", handler);
        return () => window.removeEventListener("resize", handler);
    }, []);
}

// Pattern 2: Closures holding large objects
// WRONG: Interval keeps reference to huge data
const hugeData = loadHugeDataset();
setInterval(() => {
    console.log(hugeData.length);  // hugeData never GC'd
}, 1000);

// CORRECT: Extract what you need
const dataLength = loadHugeDataset().length;
setInterval(() => {
    console.log(dataLength);
}, 1000);

// Pattern 3: Map/Set growing unbounded
// WRONG: Cache grows forever
const cache = new Map<string, Data>();
function getOrFetch(key: string): Data {
    if (!cache.has(key)) cache.set(key, fetch(key));
    return cache.get(key)!;
}

// CORRECT: LRU cache with size limit
import { LRUCache } from "lru-cache";
const cache = new LRUCache<string, Data>({ max: 1000 });
```

## Common Mistakes

```python
# WRONG: Keeping references in long-lived objects
class Service:
    def __init__(self):
        self.request_history = []  # Grows with every request

    def handle(self, request):
        self.request_history.append(request)  # Never trimmed!

# CORRECT: Bounded history
from collections import deque
class Service:
    def __init__(self):
        self.request_history = deque(maxlen=1000)  # Auto-evicts old entries
```

```go
// WRONG: Unbuffered channel in goroutine
go func() {
    result := doWork()
    ch <- result  // Blocks forever if no one reads!
}()

// CORRECT: Buffered channel or select with context
ch := make(chan Result, 1)  // Buffered — goroutine can write and exit
go func() {
    ch <- doWork()
}()
```

## Gotchas
- Python's `__del__` method prevents garbage collection of circular references (fixed in Python 3.4+ with PEP 442)
- Java's `OutOfMemoryError` doesn't always mean heap is full — it could be metaspace, direct buffers, or native memory
- Go goroutines are cheap (2KB stack) but 100,000 goroutines = 200MB minimum — always use cancellation
- JavaScript closures capture variables by reference, not value — `let` in loops prevents the classic closure bug
- `tracemalloc` in Python only tracks allocations after `start()` — start early in the process
- Redis/memory caches can mask application memory leaks by offloading — monitor total memory, not just heap
- Profilers add overhead — use sampling profilers (py-spy, async-profiler) in production, not instrumentation
- `docker stats` and `kubectl top` show container-level memory — RSS (resident set size) is the real usage metric

## Related
- performance/caching-strategies.md
- performance/database-optimization.md
- performance/connection-pooling.md
- rust/stdlib/error-handling.md
