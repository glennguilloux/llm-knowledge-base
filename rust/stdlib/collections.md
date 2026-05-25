---
id: "rust-stdlib-collections"
title: "Collections and Iterators"
language: "rust"
category: "stdlib"
tags: ["Vec", "HashMap", "BTreeMap", "HashSet", "iterator", "collect", "entry"]
version: "1.75+"
retrieval_hint: "Vec HashMap BTreeMap HashSet iterator map filter collect entry API"
last_verified: "2026-05-24"
confidence: "high"
---

# Collections and Iterators

## When to Use
- Storing variable-size data (lists, maps, sets)
- Transforming sequences of data with iterator chains
- Building lookup tables and caches
- Processing streams of items efficiently

## Standard Pattern

```rust
use std::collections::{HashMap, BTreeMap, HashSet, BTreeSet};

fn main() {
    // Vec — dynamic array
    let mut numbers: Vec<i32> = Vec::new();
    numbers.push(1);
    numbers.push(2);
    numbers.push(3);
    let sum: i32 = numbers.iter().sum();

    // Vec with initial values
    let names = vec!["Alice", "Bob", "Charlie"];

    // HashMap — O(1) lookup
    let mut scores: HashMap<String, i32> = HashMap::new();
    scores.insert("Alice".into(), 95);
    scores.insert("Bob".into(), 87);

    // Entry API — insert or update atomically
    scores.entry("Alice".into()).and_modify(|e| *e += 5).or_insert(70);
    scores.entry("Dave".into()).and_modify(|e| *e += 5).or_insert(70);

    // BTreeMap — sorted by key
    let mut ordered: BTreeMap<&str, i32> = BTreeMap::new();
    ordered.insert("z", 1);
    ordered.insert("a", 2);
    for (key, value) in &ordered {
        println!("{}: {}", key, value); // prints in sorted order
    }

    // HashSet — unique values, O(1) membership test
    let mut seen: HashSet<String> = HashSet::new();
    seen.insert("Alice".into());
    let is_new = seen.insert("Alice".into()); // returns false
    println!("Is new: {}", !is_new);

    // Iterator chains (lazy — nothing runs until collected)
    let doubled: Vec<i32> = vec![1, 2, 3, 4, 5]
        .iter()
        .filter(|&&x| x % 2 == 0)
        .map(|&x| x * 2)
        .collect();
    println!("{:?}", doubled); // [4, 8]

    // fold — accumulate into a single value
    let product = vec![1, 2, 3, 4].iter().fold(1, |acc, &x| acc * x);
    println!("Product: {}", product); // 24

    // Enumerate for index + value
    for (i, name) in names.iter().enumerate() {
        println!("{}: {}", i, name);
    }

    // Chaining iterators
    let a = vec![1, 2, 3];
    let b = vec![4, 5, 6];
    let combined: Vec<&i32> = a.iter().chain(b.iter()).collect();

    // Zip two iterators
    let keys = vec!["a", "b", "c"];
    let values = vec![1, 2, 3];
    let map: HashMap<&str, i32> = keys.into_iter().zip(values).collect();

    // FlatMap for nested structures
    let nested = vec![vec![1, 2], vec![3, 4], vec![5]];
    let flat: Vec<&i32> = nested.iter().flat_map(|v| v.iter()).collect();

    // any / all
    let has_negative = numbers.iter().any(|&x| x < 0);
    let all_positive = numbers.iter().all(|&x| x > 0);

    // take / skip for pagination
    let page: Vec<&i32> = numbers.iter().skip(1).take(2).collect();
}
```

## Common Mistakes

```rust
// WRONG: Indexing Vec with [] — panics on out of bounds
let v = vec![1, 2, 3];
let val = v[10]; // panics!

// CORRECT: Use .get() for safe access
let v = vec![1, 2, 3];
match v.get(10) {
    Some(val) => println!("{}", val),
    None => println!("Index out of bounds"),
}

// WRONG: Modifying collection while iterating
let mut v = vec![1, 2, 3, 4, 5];
for val in &v {
    if *val > 3 {
        v.push(*val * 2); // ERROR: cannot borrow as mutable
    }
}

// CORRECT: Collect modifications separately, then extend
let mut v = vec![1, 2, 3, 4, 5];
let extras: Vec<i32> = v.iter().filter(|&&x| x > 3).map(|&x| x * 2).collect();
v.extend(extras);

// WRONG: Using HashMap when order matters
let mut map = HashMap::new();
map.insert("c", 1);
map.insert("a", 2);
map.insert("b", 3);
// Iteration order is non-deterministic!

// CORRECT: Use BTreeMap for ordered iteration
let mut map = BTreeMap::new();
map.insert("c", 1);
map.insert("a", 2);
map.insert("b", 3);
// Iterates in sorted key order

// WRONG: .collect() into wrong type
let v = vec![1, 2, 3];
let result: HashSet<i32> = v.iter().collect(); // ERROR: expected HashSet, got &i32

// CORRECT: Dereference or use map
let result: HashSet<i32> = v.iter().copied().collect();

// WRONG: Using contains() on Vec for membership testing (O(n))
let v = vec![1, 2, 3, 4, 5];
if v.contains(&3) { /* slow for large vecs */ }

// CORRECT: Convert to HashSet for O(1) lookups
let set: HashSet<i32> = v.into_iter().collect();
if set.contains(&3) { /* fast */ }
```

## Gotchas
- Iterators are lazy — nothing happens until `.collect()`, `.for_each()`, or `.count()`
- `.iter()` yields `&T`, `.iter_mut()` yields `&mut T`, `.into_iter()` yields `T`
- `entry()` API is the idiomatic way to insert-or-update in HashMap
- `.collect()` infers the target type from context — annotate the variable type
- `Vec::with_capacity(n)` pre-allocates — avoids reallocations when size is known
- `.windows(n)` and `.chunks(n)` for sliding window and batch processing
- `retain()` is the idiomatic way to filter in-place
- `sort_by_key` and `sort_unstable` are faster than `sort` for most cases

## Related
- rust/stdlib/ownership.md
- rust/stdlib/traits.md
- rust/stdlib/result-option.md
