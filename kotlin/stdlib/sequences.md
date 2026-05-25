---
id: "kotlin-stdlib-sequences"
title: "Kotlin Sequences: Lazy Evaluation and Performance"
language: "kotlin"
category: "stdlib"
tags: ["kotlin", "sequences", "lazy", "yield", "asSequence", "performance"]
version: "1.9+"
retrieval_hint: "kotlin Sequence vs List lazy evaluation sequence yield asSequence when to use sequences for performance"
last_verified: "2026-05-24"
confidence: "high"
---

# Kotlin Sequences: Lazy Evaluation and Performance

## When to Use
- Processing large collections where intermediate results would waste memory
- Chaining multiple transformations (map, filter) on large datasets
- Generating infinite sequences with `yield`
- When you only need the first few results from a large computation
- Performance optimization — avoiding intermediate collection allocation

## Standard Pattern

```kotlin
// Sequence is lazy — no intermediate collections created
val result = listOf(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    .asSequence()           // Convert to Sequence
    .filter { it % 2 == 0 } // Not executed yet — lazy!
    .map { it * it }        // Not executed yet — lazy!
    .take(3)                // Only take first 3
    .toList()               // Terminal operation — triggers execution

// Compare with eager List operations (creates intermediate collections):
val eager = listOf(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    .filter { it % 2 == 0 } // Creates new List: [2, 4, 6, 8, 10]
    .map { it * it }        // Creates new List: [4, 16, 36, 64, 100]
    .take(3)                // Creates new List: [4, 16, 36]

// Sequence with yield — generate values on demand
fun fibonacci(): Sequence<Long> = sequence {
    var a = 0L
    var b = 1L
    while (true) {
        yield(a)
        val temp = a + b
        a = b
        b = temp
    }
}
val first10 = fibonacci().take(10).toList()
// [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

// Infinite sequence of natural numbers
fun naturals(): Sequence<Int> = sequence {
    var n = 1
    while (true) {
        yield(n++)
    }
}

// Performance comparison with large list
val largeList = (1..1_000_000).toList()

// Eager: creates 3 intermediate collections
val eagerResult = largeList
    .filter { it % 2 == 0 }    // 500K element list
    .map { it * it }           // 500K element list
    .take(10)                  // 10 element list
    .toList()

// Lazy: processes one element at a time, stops after finding 10
val lazyResult = largeList
    .asSequence()
    .filter { it % 2 == 0 }
    .map { it * it }
    .take(10)
    .toList()
```

## Common Mistakes

```kotlin
// WRONG: Using Sequence for small collections (unnecessary overhead)
val small = listOf(1, 2, 3, 4, 5)
    .asSequence()
    .filter { it > 2 }
    .toList()  // Sequence overhead not worth it for 5 elements

// CORRECT: Use List operations for small collections
val small = listOf(1, 2, 3, 4, 5)
    .filter { it > 2 }

// WRONG: Forgetting terminal operation (sequence never executes)
val seq = listOf(1, 2, 3).asSequence().map { it * 2 }
// seq is still a Sequence — nothing has been computed!

// CORRECT: Add a terminal operation
val result = listOf(1, 2, 3).asSequence().map { it * 2 }.toList()

// WRONG: Using first() on potentially empty sequence
val empty = emptyList<Int>().asSequence()
val item = empty.first()  // Throws NoSuchElementException

// CORRECT: Use firstOrNull()
val item = empty.firstOrNull()  // Returns null

// WRONG: Iterating a sequence multiple times
val seq = listOf(1, 2, 3).asSequence().map { it * 2 }
seq.toList()  // First iteration — OK
seq.toList()  // Second iteration — re-evaluates (may be expensive!)

// CORRECT: Materialize to List if you need multiple iterations
val list = listOf(1, 2, 3).asSequence().map { it * 2 }.toList()
list.toList()  // Just returns the list
```

## Gotchas
- Sequences are **lazy** — no computation happens until a terminal operation (`toList()`, `first()`, `count()`, `forEach`) is called.
- Each element flows through the entire chain before the next element is processed. This is called "element-by-element" or "pipelined" execution.
- `asSequence()` converts a `List` to a `Sequence`. The original list is not modified.
- `sequence { }` builder with `yield()` creates a Sequence from scratch. `yield(value)` suspends and emits a value.
- Sequences do NOT support random access. `elementAt(n)` iterates from the beginning — O(n).
- For small collections (<100 elements), List operations are often faster due to Sequence overhead.
- Sequences shine with large collections + multiple chained operations + early termination (`take`, `first`, `find`).
- A Sequence can only be iterated once (unless it's backed by a collection). After terminal operation, it's consumed.
- `generateSequence(seed) { next }` creates a sequence from a seed and a next-value function.

## Related
- kotlin/stdlib/collections.md
- kotlin/stdlib/functions-lambdas.md
- kotlin/stdlib/coroutines.md
