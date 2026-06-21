---
id: "python-concurrency-asyncio-taskgroup"
title: "asyncio.TaskGroup and Structured Concurrency (3.11+)"
language: "python"
category: "concurrency"
subcategory: "asyncio"
tags: ["asyncio", "taskgroup", "structured-concurrency", "python3.11", "exception-group", "cancel"]
version: "3.11+"
retrieval_hint: "asyncio TaskGroup structured concurrency exception group gather task cancel timeout"
last_verified: "2026-05-25"
confidence: "high"
---

# asyncio.TaskGroup and Structured Concurrency (3.11+)

## When to Use
- Managing multiple concurrent tasks where failure of one should cancel the others
- Replacing `asyncio.gather()` when you need different coroutines (not just the same one)
- Ensuring all child tasks complete (or are cancelled) before the parent continues
- Working with exception groups for granular error handling
- Building reliable background task supervisors

## Standard Pattern

```python
import asyncio
from asyncio import TaskGroup, ExceptionGroup


async def fetch_data(url: str) -> dict:
    """Simulate fetching data from an API."""
    await asyncio.sleep(1)
    if "bad" in url:
        raise ValueError(f"Failed to fetch {url}")
    return {"url": url, "status": 200}


async def main_with_taskgroup():
    """Structured concurrency with TaskGroup."""
    try:
        async with TaskGroup() as tg:
            task1 = tg.create_task(fetch_data("/api/users"))
            task2 = tg.create_task(fetch_data("/api/posts"))
            task3 = tg.create_task(fetch_data("/api/bad"))  # This will fail

        # All tasks complete here, or all are cancelled on any failure
        print(f"Task1 result: {task1.result()}")
        print(f"Task2 result: {task2.result()}")

    except* ValueError as eg:
        # Handle ONLY ValueError exceptions from the group
        for exc in eg.exceptions:
            print(f"ValueError caught: {exc}")

    except* Exception as eg:
        # Handle any other exceptions
        for exc in eg.exceptions:
            print(f"Other error: {exc}")


async def main_with_timeout():
    """TaskGroup with per-task timeout."""
    async with TaskGroup() as tg:
        task1 = tg.create_task(
            asyncio.wait_for(fetch_data("/api/users"), timeout=2.0)
        )
        task2 = tg.create_task(
            asyncio.wait_for(fetch_data("/api/posts"), timeout=0.5)  # Might time out
        )

    try:
        print(f"Result: {task1.result()}")
    except Exception as e:
        print(f"Task failed: {e}")


async def nested_taskgroups():
    """Nested TaskGroups — inner failures DO NOT cancel outer group."""
    try:
        async with TaskGroup() as outer:
            tg1 = asyncio.TaskGroup()
            tg2 = asyncio.TaskGroup()
            async with tg1 as tg1_, tg2 as tg2_:
                t1 = tg1_.create_task(fetch_data("/api/a"))
                t2 = tg2_.create_task(fetch_data("/api/bad"))
                t3 = tg2_.create_task(fetch_data("/api/c"))

        # tg2's failure only cancels tg2's tasks, not tg1's
        print(f"Task 1 succeeded: {t1.result()}")

    except* ValueError as eg:
        print(f"Got {len(eg.exceptions)} ValueError(s)")


asyncio.run(main_with_taskgroup())
asyncio.run(main_with_timeout())
asyncio.run(nested_taskgroups())
```

## Common Mistakes

```python
# WRONG: Using asyncio.gather() when tasks are heterogeneous
# gather() returns results in order but doesn't provide structured cancellation
async def wrong_gather():
    tasks = await asyncio.gather(
        fetch_data("/api/users"),
        fetch_data("/api/bad"),    # Fails, cancels others with return_exceptions=False
        fetch_data("/api/posts"),
    )

# CORRECT: Use TaskGroup for different tasks with structured exception handling
async def correct_taskgroup():
    async with TaskGroup() as tg:
        t1 = tg.create_task(fetch_data("/api/users"))
        t2 = tg.create_task(fetch_data("/api/bad"))
        t3 = tg.create_task(fetch_data("/api/posts"))
    # If t2 failed, t1 and t3 are auto-cancelled
    # All results are available (or exceptions propagated) here

# WRONG: Using create_task() directly without TaskGroup supervision
# Tasks become fire-and-forget — exceptions are silently swallowed
async def wrong_create_task():
    task = asyncio.create_task(fetch_data("/api/users"))
    await asyncio.sleep(2)
    # If fetch_data failed, the exception is only logged, not raised

# CORRECT: Use TaskGroup if you want supervision
async def correct_supervised():
    async with TaskGroup() as tg:
        task = tg.create_task(fetch_data("/api/users"))

    # Exception is re-raised here if task failed
    result = task.result()

# WRONG: Mixing create_task inside TaskGroup — defeats cancellation
async def wrong_mix(tg: TaskGroup):
    task = asyncio.create_task(fetch_data("/api/leaked"))
    tg.create_task(fetch_data("/api/proper"))
    # The create_task task is NOT managed by TaskGroup — it'll leak

# CORRECT: Only use tg.create_task() inside TaskGroup
async def correct_only_tg():
    async with TaskGroup() as tg:
        task = tg.create_task(fetch_data("/api/proper"))
```

## Gotchas
- **TaskGroup is STRICT — one failure cancels all:** As soon as any task raises an unhandled exception, TaskGroup cancels every other task in the group. This is by design (fail-fast), but surprising if you expected `gather(return_exceptions=True)` behavior. For partial-failure tolerance, use `asyncio.gather()` with `return_exceptions=True` instead.
- **Nested TaskGroups create isolation boundaries:** A failure in an inner TaskGroup cancels only the inner group's tasks. The outer group continues. This lets you build fault isolation: "if this subtask fails, don't kill the whole operation."
- **ExceptionGroup matching with `except*`:** Python 3.11+ requires `except*` (not `except`) to catch exceptions from `ExceptionGroup`. Using plain `except ValueError` won't catch `ValueError` wrapped in an ExceptionGroup. You must use `except* ValueError as eg` and iterate `eg.exceptions`.
- **TaskGroup as async context manager:** The `async with TaskGroup() as tg:` block won't exit until ALL child tasks complete (or are cancelled). Don't put long-running code after `create_task()` inside the block unless you intend to wait.
- **Results access after the block:** After the `async with` block exits, task results are available via `task.result()`. If the task was cancelled by another task's failure, `task.result()` raises `CancelledError`, not the original exception.

## Related
- python/concurrency/asyncio-basics.md
- python/stdlib/asyncio-basics.md
