---
id: "performance-python-profiling"
title: "Python Performance Profiling"
language: "multi"
category: "performance"
tags: ["python", "profiling", "cprofile", "line-profiler", "memory", "performance"]
version: "3.10+"
retrieval_hint: "Python performance profiling cProfile line_profiler pyinstrument memory profiling bottleneck hotspot tracing sampling"
last_verified: "2026-06-20"
confidence: "medium"
---

# Python Performance Profiling

## When to Use
- Diagnosing slow Python code before changing algorithms or adding caches
- Finding hot functions, call stacks, and allocation-heavy lines in services
- Comparing relative impact of candidate optimizations with the same workload
- Profiling CPU-bound, I/O-bound, and memory-heavy code paths separately

## Standard Pattern

```python
# === cProfile: CPU-time profiling ===
import cProfile
import io
import pstats

def run_workload():
    return expensive_function()

profiler = cProfile.Profile()
profiler.enable()
try:
    result = run_workload()
finally:
    profiler.disable()

stats = pstats.Stats(profiler).sort_stats("cumtime")
stats.print_stats(20)
```

```python
# === cProfile from the command line ===
# python -m cProfile -o profile.prof app.py
# python -m pstats profile.prof
# (pstats) strip
# (pstats) sort cumtime
# (pstats) stats 20
```

```python
# === line_profiler: line-level hotspots ===
# pip install line_profiler
from line_profiler import LineProfiler

def profile_lines():
    lp = LineProfiler()
    lp_wrapper = lp(expensive_function)
    result = lp_wrapper()
    lp.print_stats()
    return result
```

```python
# === tracemalloc: allocation profiling ===
import tracemalloc

tracemalloc.start()

result = build_large_response()

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics("lineno")
for stat in top_stats[:10]:
    print(stat)

tracemalloc.stop()
```

## Common Mistakes

```python
# WRONG: Guessing the bottleneck from code inspection
slow_part = guess_the_slow_part()
optimize(slow_part)

# CORRECT: Profile the real workload first
import cProfile
profiler = cProfile.Profile()
profiler.enable()
try:
    run_request()
finally:
    profiler.disable()
pstats.Stats(profiler).sort_stats("cumtime").print_stats(20)
```

```python
# WRONG: Profiling setup code instead of steady-state work
profiler.enable()
start_database()
load_configuration()
run_request()
profiler.disable()

# CORRECT: Warm up dependencies, then profile the target path
start_database()
load_configuration()
run_request()  # warm-up

profiler.enable()
try:
    for _ in range(10):
        run_request()
finally:
    profiler.disable()
```

```python
# WRONG: Using time.time() around one noisy run
start = time.time()
run_request()
print(time.time() - start)

# CORRECT: Use a profiler and repeat under comparable conditions
profiler = cProfile.Profile()
profiler.enable()
try:
    for _ in range(5):
        run_request()
finally:
    profiler.disable()
pstats.Stats(profiler).sort_stats("cumtime").print_stats()
```

```python
# WRONG: Ignoring allocation pressure in CPU profiling
# A function looks fast in cProfile but causes frequent garbage collection

# CORRECT: Pair CPU profiling with allocation profiling
import cProfile
import tracemalloc

tracemalloc.start()
profiler = cProfile.Profile()
profiler.enable()
try:
    result = run_workload()
finally:
    profiler.disable()
pstats.Stats(profiler).sort_stats("cumtime").print_stats(20)
print(tracemalloc.take_snapshot().statistics("lineno")[:10])
```

## Gotchas
- cProfile has overhead, so treat it as a diagnostic run rather than a production timing source
- Cumulative time shows time spent in a function and its callees; inline time shows only the function body
- Sampling profilers are lighter than tracing profilers but can miss very short-lived calls
- I/O waits can look like CPU time in some profiles; separate network, disk, lock, and CPU bottlenecks before optimizing
- `tracemalloc` reports Python allocations, not native extension memory unless the extension exposes allocation hooks
- Profiling only one request shape can hide slow paths triggered by different inputs or cache states

## Related
- performance/caching-strategies.md
- performance/database-optimization.md
- performance/memory-patterns.md
