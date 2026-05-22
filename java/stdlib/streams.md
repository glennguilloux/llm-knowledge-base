---
id: "java-stdlib-streams"
title: "Java Stream API"
language: "java"
category: "stdlib"
subcategory: "functional"
tags: ["stream", "functional", "map", "filter", "reduce", "collect"]
version: "17+"
retrieval_hint: "Java stream map filter reduce collect functional"
last_verified: "2026-05-22"
confidence: "high"
---

# Java Stream API

## When to Use
- Processing collections with functional operations
- Filtering, mapping, and reducing data
- Parallel processing of large datasets
- Chaining multiple operations

## Standard Pattern

```java
import java.util.*;
import java.util.stream.*;

// Filter and collect
List<String> names = List.of("Alice", "Bob", "Charlie", "David");
List<String> longNames = names.stream()
    .filter(name -> name.length() > 3)
    .collect(Collectors.toList());
// ["Alice", "Charlie", "David"]

// Map transformation
List<Integer> lengths = names.stream()
    .map(String::length)
    .collect(Collectors.toList());
// [5, 3, 7, 5]

// Reduce
int totalLength = names.stream()
    .mapToInt(String::length)
    .sum();
// 20

// Collectors
Map<Integer, List<String>> byLength = names.stream()
    .collect(Collectors.groupingBy(String::length));
// {3=["Bob"], 5=["Alice", "David"], 7=["Charlie"]}

String joined = names.stream()
    .collect(Collectors.joining(", "));
// "Alice, Bob, Charlie, David"

// Optional
Optional<String> first = names.stream()
    .filter(name -> name.startsWith("A"))
    .findFirst();
first.ifPresent(System.out::println);

// Parallel stream
long count = names.parallelStream()
    .filter(name -> name.length() > 3)
    .count();

// Custom collector
List<String> collected = names.stream()
    .collect(Collectors.collectingAndThen(
        Collectors.toList(),
        Collections::unmodifiableList
    ));
```

## Common Mistakes

```java
// WRONG: Reusing stream
Stream<String> stream = names.stream();
long count = stream.count();
stream.forEach(System.out::println);  // IllegalStateException!

// CORRECT: Create new stream each time
long count = names.stream().count();
names.stream().forEach(System.out::println);

// WRONG: Using stream for side effects
List<String> results = new ArrayList<>();
names.stream().forEach(name -> results.add(name.toUpperCase()));  // Not functional!

// CORRECT: Use collect
List<String> results = names.stream()
    .map(String::toUpperCase)
    .collect(Collectors.toList());

// WRONG: Not handling Optional
String result = names.stream()
    .filter(name -> name.startsWith("Z"))
    .findFirst()
    .get();  // NoSuchElementException!

// CORRECT: Use orElse or ifPresent
String result = names.stream()
    .filter(name -> name.startsWith("Z"))
    .findFirst()
    .orElse("Not found");
```

## Gotchas
- Streams are lazy — intermediate operations don't execute until terminal operation
- Streams can only be consumed once
- `parallelStream()` uses ForkJoinPool — not always faster for small datasets
- Use `mapToInt()`, `mapToLong()`, `mapToDouble()` for primitive streams
- `Collectors.toUnmodifiableList()` for immutable results
- `Stream.of()` for creating streams from values
- `Files.lines()` for streaming file lines

## Related
- java/stdlib/collections.md
- java/stdlib/optional.md
