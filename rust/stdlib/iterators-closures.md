---
id: "rust-stdlib-iterators-closures"
title: "Rust Iterators and Closures Deep Dive"
language: "rust"
category: "stdlib"
subcategory: "functional"
tags: ["rust", "iterator", "closure", "map", "filter", "fold", "chain"]
version: "1.75+"
retrieval_hint: "Rust iterator closure map filter fold chain collect functional"
last_verified: "2026-05-22"
confidence: "high"
---

# Rust Iterators and Closures Deep Dive

## When to Use
- Processing collections functionally (map, filter, reduce)
- Lazy evaluation of sequences (iterators are lazy by default)
- Chaining transformations without intermediate allocations
- Custom iterators for domain-specific sequences

## Standard Pattern

```rust
// --- Basic iterator patterns ---
fn process_numbers(numbers: &[i32]) -> Vec<i32> {
    numbers
        .iter()
        .filter(|&&x| x > 0)           // Keep positive
        .map(|&x| x * 2)               // Double
        .filter(|&x| x < 100)          // Remove large values
        .collect()                      // Collect into Vec
}

// --- Closures ---
fn apply_operation<F>(a: i32, b: i32, op: F) -> i32
where
    F: Fn(i32, i32) -> i32,
{
    op(a, b)
}

let add = |a, b| a + b;
let result = apply_operation(5, 3, add);

// --- Closure capturing environment ---
fn make_counter(start: i32) -> impl FnMut() -> i32 {
    let mut count = start;
    move || {
        let current = count;
        count += 1;
        current
    }
}

let mut counter = make_counter(0);
assert_eq!(counter(), 0);
assert_eq!(counter(), 1);

// --- Iterator adapters ---
fn process_users(users: &[User]) -> Vec<String> {
    users
        .iter()
        .filter(|u| u.is_active)
        .map(|u| u.name.clone())
        .collect()
}

// --- fold (reduce) ---
fn sum_positive(numbers: &[i32]) -> i32 {
    numbers
        .iter()
        .filter(|&&x| x > 0)
        .fold(0, |acc, &x| acc + x)
}

// --- Custom iterator ---
struct Counter {
    current: u32,
    max: u32,
}

impl Counter {
    fn new(max: u32) -> Self {
        Counter { current: 0, max }
    }
}

impl Iterator for Counter {
    type Item = u32;

    fn next(&mut self) -> Option<Self::Item> {
        if self.current < self.max {
            let val = self.current;
            self.current += 1;
            Some(val)
        } else {
            None
        }
    }
}

// Usage: Counter::new(5).collect::<Vec<_>>() = [0, 1, 2, 3, 4]
// Counter::new(10).filter(|x| x % 2 == 0).collect() = [0, 2, 4, 6, 8]

// --- Chaining iterators ---
fn find_admin_emails(users: &[User]) -> Vec<String> {
    users
        .iter()
        .filter(|u| u.role == Role::Admin)
        .map(|u| u.email.clone())
        .filter(|e| e.ends_with("@company.com"))
        .collect()
}

// --- enumerate and zip ---
fn format_items(items: &[String]) -> Vec<String> {
    items
        .iter()
        .enumerate()
        .map(|(i, item)| format!("{}. {}", i + 1, item))
        .collect()
}
```

## Common Mistakes

```rust
// WRONG: Collecting unnecessarily (intermediate allocation)
let filtered: Vec<i32> = numbers.iter().filter(|&&x| x > 0).cloned().collect();
let mapped: Vec<i32> = filtered.iter().map(|x| x * 2).collect();

// CORRECT: Chain without intermediate collection
let result: Vec<i32> = numbers.iter()
    .filter(|&&x| x > 0)
    .map(|&x| x * 2)
    .collect();

// WRONG: Using iter() when you need ownership
let names: Vec<String> = users.iter().map(|u| u.name.clone()).collect();  // Clones

// CORRECT: Use into_iter() for ownership
let names: Vec<String> = users.into_iter().map(|u| u.name).collect();  // Moves

// WRONG: Closure that borrows when it should move
let mut data = vec![1, 2, 3];
let closure = || data.push(4);  // Borrows mutably
closure();
// data is still borrowed!

// CORRECT: Use move keyword when needed
let mut data = vec![1, 2, 3];
let mut closure = move || data.push(4);
closure();

// WRONG: Using for loop when iterator is cleaner
let mut result = Vec::new();
for x in &numbers {
    if *x > 0 {
        result.push(x * 2);
    }
}

// CORRECT: Use iterator chain
let result: Vec<i32> = numbers.iter().filter(|&&x| x > 0).map(|&x| x * 2).collect();
```

## Gotchas
- Iterators are lazy — nothing happens until `.collect()`, `.for_each()`, or other consuming adapter
- `iter()` gives `&T`; `iter_mut()` gives `&mut T`; `into_iter()` gives `T` (ownership)
- Closures implement `Fn`, `FnMut`, or `FnOnce` — inferred by the compiler
- `move` keyword forces closure to take ownership of captured variables
- `.cloned()` converts `&T` to `T` for `Clone` types
- `.enumerate()` returns `(index, &item)` tuples
- `.zip()` combines two iterators into pairs
- `.chain()` concatenates two iterators
- `.flat_map()` maps and flattens (like `flatMap` in other languages)

## Related
- rust/stdlib/collections.md
- rust/stdlib/ownership.md
- rust/stdlib/result-option.md
