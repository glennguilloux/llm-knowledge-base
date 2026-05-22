---
id: "java-stdlib-collections"
title: "Java Collections Framework"
language: "java"
category: "stdlib"
subcategory: "collections"
tags: ["collections", "list", "map", "set", "arraylist", "hashmap"]
version: "17+"
retrieval_hint: "Java collections list map set arraylist hashmap"
last_verified: "2026-05-22"
confidence: "high"
---

# Java Collections Framework

## When to Use
- Storing and manipulating groups of objects
- Choosing the right data structure for performance
- Working with dynamic arrays, hash tables, and ordered sets

## Standard Pattern

```java
import java.util.*;

// List - ordered, allows duplicates
List<String> names = new ArrayList<>();
names.add("Alice");
names.add("Bob");
names.add("Alice");  // Allowed
String first = names.get(0);
names.remove(0);

// Immutable list (Java 9+)
List<String> immutable = List.of("Alice", "Bob", "Charlie");

// Set - no duplicates
Set<String> unique = new HashSet<>();
unique.add("Alice");
unique.add("Alice");  // Ignored
boolean hasAlice = unique.contains("Alice");

// Immutable set
Set<String> immutableSet = Set.of("Alice", "Bob");

// Map - key-value pairs
Map<String, Integer> ages = new HashMap<>();
ages.put("Alice", 30);
ages.put("Bob", 25);
int age = ages.getOrDefault("Charlie", 0);
ages.putIfAbsent("Alice", 99);  // Won't overwrite

// Immutable map
Map<String, Integer> immutableMap = Map.of("Alice", 30, "Bob", 25);

// Iteration
for (String name : names) {
    System.out.println(name);
}

ages.forEach((key, value) -> System.out.println(key + ": " + value));

// Sorting
List<Integer> numbers = new ArrayList<>(List.of(3, 1, 4, 1, 5));
Collections.sort(numbers);  // In-place
numbers.sort(Comparator.naturalOrder());
```

## Common Mistakes

```java
// WRONG: Using raw types
List list = new ArrayList();  // No type safety!
list.add("hello");
list.add(42);  // Compiles but ClassCastException later

// CORRECT: Use generics
List<String> list = new ArrayList<>();
list.add("hello");
// list.add(42);  // Compile error!

// WRONG: Modifying immutable list
List<String> list = List.of("Alice", "Bob");
list.add("Charlie");  // UnsupportedOperationException!

// CORRECT: Use mutable ArrayList
List<String> list = new ArrayList<>(List.of("Alice", "Bob"));
list.add("Charlie");

// WRONG: Using == for object comparison
if (names.get(0) == "Alice")  // Reference comparison!

// CORRECT: Use .equals()
if ("Alice".equals(names.get(0)))
```

## Gotchas
- `List.of()`, `Set.of()`, `Map.of()` create immutable collections
- `ArrayList` is faster for random access; `LinkedList` for insertions
- `HashMap` has O(1) average lookup; `TreeMap` has O(log n) sorted
- `HashSet` uses `hashCode()` and `equals()` for deduplication
- Use `Collections.unmodifiableList()` to wrap mutable list as immutable
- `ConcurrentHashMap` for thread-safe map operations

## Related
- java/stdlib/streams.md
- java/stdlib/optional.md
