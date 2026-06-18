---
id: "kotlin-stdlib-collections"
title: "Kotlin Collections: List, Map, Set, and Operations"
language: "kotlin"
category: "stdlib"
tags: ["kotlin", "collections", "list", "map", "set", "filter", "map-function", "groupBy"]
version: "1.9+"
retrieval_hint: "kotlin collections listOf mutableListOf mapOf filter map groupBy flatMap partition"
last_verified: "2026-05-24"
confidence: "high"
---

# Kotlin Collections: List, Map, Set, and Operations

## When to Use
- Working with collections in Kotlin — the default is immutable
- Transforming, filtering, or grouping data
- Migrating from Java Streams to Kotlin collection operations
- Understanding the difference between mutable and immutable collection types

## Standard Pattern

```kotlin
// Immutable collections (default — preferred)
val numbers: List<Int> = listOf(1, 2, 3, 4, 5)
val names: Set<String> = setOf("Alice", "Bob", "Charlie")
val scores: Map<String, Int> = mapOf("Alice" to 95, "Bob" to 87)

// Mutable collections (when you need to modify)
val mutableList: MutableList<Int> = mutableListOf(1, 2, 3)
mutableList.add(4)
mutableList.removeAt(0)

val mutableMap: MutableMap<String, Int> = mutableMapOf("a" to 1)
mutableMap["b"] = 2

// Filtering
val even = numbers.filter { it % 2 == 0 }           // [2, 4]
val greaterThan3 = numbers.filter { it > 3 }         // [4, 5]

// Mapping (transform each element)
val doubled = numbers.map { it * 2 }                 // [2, 4, 6, 8, 10]
val nameLengths = names.map { it.length }            // [5, 3, 7]

// groupBy — group elements by a key
val words = listOf("apple", "banana", "avocado", "cherry", "blueberry")
val byFirstLetter = words.groupBy { it.first() }
// {a=[apple, avocado], b=[banana, blueberry], c=[cherry]}

// associate — create a map from a list
val nameToLength = names.associate { it to it.length }
// {Alice=5, Bob=3, Charlie=7}

// partition — split into two lists based on predicate
val (evens, odds) = numbers.partition { it % 2 == 0 }
// evens = [2, 4], odds = [1, 3, 5]

// flatMap — map then flatten
val nested = listOf(listOf(1, 2), listOf(3, 4))
val flat = nested.flatMap { it }                     // [1, 2, 3, 4]
val chars = names.flatMap { it.toList() }            // [A, l, i, c, e, B, o, b, ...]

// Useful operations
val sum = numbers.sum()                              // 15
val max = numbers.maxOrNull()                        // 5
val sorted = names.sorted()                          // [Alice, Bob, Charlie]
val distinct = listOf(1, 1, 2, 3).distinct()         // [1, 2, 3]
val anyEven = numbers.any { it % 2 == 0 }            // true
val allEven = numbers.all { it % 2 == 0 }            // false
val firstEven = numbers.first { it % 2 == 0 }        // 2
```

## Common Mistakes

```kotlin
// WRONG: Trying to add to an immutable list
val list = listOf(1, 2, 3)
// list.add(4)  // Compile error — listOf returns read-only List

// CORRECT: Use mutableListOf for mutable collections
val list = mutableListOf(1, 2, 3)
list.add(4)  // OK

// WRONG: Using Java-style for loops
for (i in 0 until numbers.size) {
    println(numbers[i])
}

// CORRECT: Use Kotlin idiomatic iteration
for (number in numbers) {
    println(number)
}

// WRONG: map vs flatMap confusion
val nested = listOf(listOf(1, 2), listOf(3, 4))
val wrong = nested.map { it }  // Returns List<List<Int>>

// CORRECT: Use flatMap to flatten
val correct = nested.flatMap { it }  // Returns List<Int>

// WRONG: first() on empty list throws NoSuchElementException
val empty = emptyList<Int>()
val item = empty.first()  // Throws!

// CORRECT: Use firstOrNull() for safety
val item = empty.firstOrNull()  // Returns null

// WRONG: Modifying a collection while iterating
val items = mutableListOf(1, 2, 3, 4)
for (item in items) {
    if (item % 2 == 0) items.remove(item)  // ConcurrentModificationException
}

// CORRECT: Use removeAll with predicate
items.removeAll { it % 2 == 0 }
```

## Gotchas
- `listOf()` returns a read-only `List` — not a `MutableList`. You cannot add/remove elements.
- `mutableListOf()` returns a `MutableList` which supports add/remove/set operations.
- `map { }` transforms each element 1:1. `flatMap { }` transforms each element into a collection and flattens the result.
- `groupBy` returns a `Map<K, List<V>>` — each key maps to a list of matching elements.
- `associate` returns a `Map<K, V>` — each element maps to a single key-value pair (last wins on duplicate keys).
- `partition` returns a `Pair<List, List>` — destructure with `val (matching, notMatching) = list.partition { }`.
- Kotlin collection operations return NEW collections (immutable ones). They don't modify the original.
- `first()` and `last()` throw on empty collections. Use `firstOrNull()` and `lastOrNull()` for safety.
- The `to` infix function creates a `Pair`: `"key" to "value"` is equivalent to `Pair("key", "value")`.

## Related
- kotlin/stdlib/basics.md
- kotlin/stdlib/sequences.md
- kotlin/stdlib/functions-lambdas.md
