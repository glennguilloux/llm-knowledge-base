---
id: "java-stdlib-map-operations"
title: "Java Map Operations"
language: "java"
category: "stdlib"
subcategory: "collections"
tags: ["map", "hashmap", "linkedhashmap", "computemerge", "compute-if-absent", "merge"]
version: "17+"
retrieval_hint: "Java HashMap computeIfAbsent merge getOrDefault iteration order LinkedHashMap"
last_verified: "2026-05-24"
confidence: "high"
---

# Java Map Operations

## When to Use
- Key-value associations with O(1) lookup (HashMap)
- Tracking insertion order ( LinkedHashMap)
- Atomic-style per-key compute/update (computeIfAbsent, merge)
- Default values for missing keys (getOrDefault)
- Grouping and counting patterns

## Standard Pattern

```java
import java.util.*;
import java.util.stream.Collectors;

public class MapOperations {

    // Basic HashMap operations
    public static Map<String, Integer> wordCount(String text) {
        Map<String, Integer> counts = new HashMap<>();
        for (String word : text.toLowerCase().split("\\s+")) {
            counts.merge(word, 1, Integer::sum);  // Increment or set to 1
        }
        return counts;
    }

    // computeIfAbsent: lazily create values on first access
    public static Map<String, List<String>> groupByFirstLetter(List<String> words) {
        Map<String, List<String>> groups = new HashMap<>();
        for (String word : words) {
            if (word == null || word.isEmpty()) continue;
            String key = word.substring(0, 1).toUpperCase();
            // computeIfAbsent returns existing or creates new ArrayList, then adds word
            groups.computeIfAbsent(key, k -> new ArrayList<>()).add(word);
        }
        return groups;
    }

    // merge: combine old and new values with a function
    public static Map<String, Integer> mergeMaps(
            Map<String, Integer> map1, Map<String, Integer> map2) {
        Map<String, Integer> result = new HashMap<>(map1);
        map2.forEach((key, value) -> result.merge(key, value, Integer::sum));
        return result;
    }

    // getOrDefault for safe access
    public static int getScore(Map<String, Integer> scores, String player) {
        return scores.getOrDefault(player, 0);
    }

    // LinkedHashMap for insertion order
    public static Map<String, Integer> orderedUserAges() {
        Map<String, Integer> ages = new LinkedHashMap<>();
        ages.put("Charlie", 35);
        ages.put("Alice", 30);
        ages.put("Bob", 25);
        // Iteration order: Charlie, Alice, Bob (insertion order preserved)
        return ages;
    }

    // computeIfPresent: only update if key exists
    public static void incrementExisting(Map<String, Integer> map, String key, int delta) {
        map.computeIfPresent(key, (k, v) -> v + delta);
        // Key won't be added if it didn't exist - unlike merge/put
    }

    public static void main(String[] args) {
        System.out.println(wordCount("the cat sat on the mat the cat"));
        System.out.println(groupByFirstLetter(List.of("apple", "avocado", "banana", "cherry")));
        System.out.println(scoreMap);
        System.out.println(orderedUserAges());
        Map<String, Integer> scores = new HashMap<>(Map.of("alice", 10));
        incrementExisting(scores, "alice", 5);
        incrementExisting(scores, "bob", 5);  // Won't add bob - key doesn't exist
        System.out.println("After increment: " + scores);
    }
}
```

## Common Mistakes

```java
// WRONG: Checking containsKey then put - two map operations, not thread-safe
if (!map.containsKey(key)) {
    map.put(key, new ArrayList<>());
}
map.get(key).add(value);  // Could still be null in concurrent access

// CORRECT: Use computeIfAbsent - single atomic operation
map.computeIfAbsent(key, k -> new ArrayList<>()).add(value);

// WRONG: Using put to increment - overwrites instead of accumulating
map.put(key, map.getOrDefault(key, 0) + 1);  // Works but verbose

// CORRECT: Use merge for accumulation
map.merge(key, 1, Integer::sum);

// WRONG: Modifying a HashMap value returned by computeIfAbsent with a null mapper
map.computeIfAbsent(key, k -> null);  // Removes the key if present, or does nothing!

// CORRECT: Always return a non-null value from computeIfAbsent's mapping function
map.computeIfAbsent(key, k -> new ArrayList<>());

// WRONG: Expecting HashMap iteration order to be sorted or consistent
Map<String, Integer> map = new HashMap<>();
map.put("b", 2); map.put("a", 1); map.put("c", 3);
// Order is hash-based and may change when map resizes

// CORRECT: Use LinkedHashMap for insertion order or TreeMap for sorted order
Map<String, Integer> ordered = new LinkedHashMap<>();
ordered.put("b", 2); ordered.put("a", 1); ordered.put("c", 3);
// Iterates in insertion order: b, a, c

// WRONG: Using computeIfPresent when you want to insert if absent
map.computeIfPresent(key, (k, v) -> v + 1);  // Does nothing if key missing!

// CORRECT: Use merge or compute instead
map.merge(key, 1, Integer::sum);  // Inserts 1 if absent, adds 1 if present
```

## Gotchas
- `computeIfAbsent` returns the **existing or newly computed value** - chain `.add()` directly on the returned collection
- If the mapping function passed to `computeIfAbsent` returns `null`, the key is **removed** (if present) or nothing happens (if absent)
- `merge(key, value, remappingFunction)` - the `remappingFunction` receives the **old value** and the **new value**; if it returns `null`, the key is removed
- `HashMap` default initial capacity is 16 with load factor 0.75 - it resizes at 12 entries, which rehashes all keys. For large maps, initialize with expected size: `new HashMap<>(expectedSize * 4 / 3 + 1)`
- When iterating a `LinkedHashMap` with access-order (third constructor arg = true), every `get()` moves that entry to the end - useful for LRU caches
- The `HashMap.compute` method (Java 8+) can compute a new value regardless of whether the key exists - but `computeIfPresent` and `computeIfAbsent` are more explicit about intent

## Related
- java/stdlib/collections.md
- java/stdlib/streams.md
