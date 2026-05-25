---
id: "rust-stdlib-iteration"
title: "Rust Iteration — iter vs into_iter vs iter_mut, map, fold, zip, chaining"
language: "rust"
category: "stdlib"
subcategory: "functional"
tags: ["rust", "iterator", "iter", "into_iter", "iter_mut", "map", "fold", "zip", "enumerate"]
version: "1.75+"
retrieval_hint: "Rust iter into_iter iter_mut map for_each collect enumerate zip chain fold iteration"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust Iteration — iter vs into_iter vs iter_mut, map, fold, zip, chaining

## When to Use
- `iter()` when you only need to read values (`&T` items)
- `into_iter()` when you need to take ownership of values (`T` items) — consumes the collection
- `iter_mut()` when you need to mutate values in place (`&mut T` items)
- `.map()` for lazy transformation (returns iterator with cloned/mapped values)
- `.for_execute()` for side effects (returns `()`, runs immediately)
- `.collect()` to materialize an iterator into a collection
- `.enumerate()` for index-value pairs, `.zip()` for pairing two iterators, `.chain()` for concatenation
- `.fold()` for custom accumulation (sum, max, build-your-own)

## Standard Pattern

```rust
use std::collections::HashMap;

// --- iter() — borrowing ---
fn sum_values(values: &[i32]) -> i32 {
    values.iter().copied().sum()
}

// --- into_iter() — ownership ---
fn sum_owned(values: Vec<i32>) -> i32 {
    values.into_iter().sum() // Consumes vec
}

// --- iter_mut() — mutation in place ---
fn double_in_place(values: &mut [i32]) {
    for v in values.iter_mut() {
        *v *= 2;
    }
}

// --- map() vs for_each() ---
fn demo_map_v_for_each() {
    // map: lazy transformation — returns new iterator (clone or move values)
    let doubles: Vec<i32> = vec![1, 2, 3]
        .iter()
        .map(|&x| x * 2)
        .collect();

    // for_each: eager side-effects — returns (), runs immediately
    let mut side_effects = Vec::new();
    vec![1, 2, 3]
        .iter()
        .for_each(|&x| side_effects.push(x * 2));

    assert_eq!(doubles, side_effects);
}

// --- enumerate ---
fn find_index(haystack: &[&str], needle: &str) -> Option<usize> {
    haystack.iter().enumerate().find(|(_, &s)| s == needle).map(|(i, _)| i)
}

// --- zip ---
fn merge(a: &[i32], b: &[f64]) -> Vec<(i32, f64)> {
    a.iter().copied()
        .zip(b.iter().copied())
        .collect() // Stops at shorter iterator
}

// --- chain ---
fn combine(a: &[i32], b: &[i32]) -> Vec<i32> {
    a.iter().chain(b.iter()).copied().collect()
}

// --- fold ---
fn longest_name(names: &[&str]) -> Option<&str> {
    names.iter().copied().fold(None, |longest, name| {
        match longest {
            None => Some(name),
            Some(current) if name.len() > current.len() => Some(name),
            _ => longest,
        }
    })
}

fn sum_with_running_log(numbers: &[i32]) -> (i32, Vec<i32>) {
    numbers.iter().copied().fold((0, Vec::new()), |(sum, mut log), x| {
        let new_sum = sum + x;
        log.push(new_sum);
        (new_sum, log)
    })
}

fn main() {
    // iter vs into_iter vs iter_mut
    let data = vec![1, 2, 3];
    println!("sum: {}", sum_values(&data));

    let owned = vec![10, 20, 30];
    println!("owned sum: {}", sum_owned(owned));
    // println!("{:?}", owned); // ERROR: moved

    let mut mutable = vec![5, 10, 15];
    double_in_place(&mut mutable);
    println!("doubled: {:?}", mutable);

    demo_map_v_for_each();

    // enumerate + find
    let fruits = ["apple", "banana", "cherry"];
    println!("banana at: {:?}", find_index(&fruits, "banana"));

    // zip
    let nums = [1, 2, 3];
    let prices = [9.99, 19.99];
    println!("pairs: {:?}", merge(&nums, &prices)); // Only 2 pairs (shorter wins)

    // chain + collect
    println!("combined: {:?}", combine(&[1, 2], &[3, 4]));

    // fold
    let names = ["Ada", "Grace", "Linus", "Margaret"];
    println!("longest: {:?}", longest_name(&names));

    let (total, log) = sum_with_running_log(&[1, 2, 3, 4]);
    println!("total: {}, running: {:?}", total, log);
}
```

## Common Mistakes

```rust
// WRONG: Using into_iter() when you need the collection after
let ids = vec![1, 2, 3];
let doubled: Vec<i32> = ids.into_iter().map(|x| x * 2).collect();
// println!("{:?}", ids); // COMPILE ERROR: ids was consumed

// CORRECT: Use iter() for read-only access
let ids = vec![1, 2, 3];
let doubled: Vec<i32> = ids.iter().map(|&x| x * 2).collect();
println!("original: {:?}", ids); // Still valid

// WRONG: Using when a sized iterator method would be clearer
let first_over_10 = numbers.iter().filter(|&&x| x > 10).map(|&x| x * 2).next();
// After .next(), the filter+map pipeline is partially consumed — confusing

// CORRECT: find() + map() is cleaner for "first match"
let first_over_10 = numbers.iter().find(|&&x| x > 10).map(|&x| x * 2);

// WRONG: Collecting to wrong type without turbofish or annotation
let collected = [1, 2, 3].iter().map(|&x| x.to_string()).collect();
// ERROR: can't infer collection type for collect()

// CORRECT: Annotate the variable or use turbofish
let collected: Vec<String> = [1, 2, 3].iter().map(|&x| x.to_string()).collect();
// Or: [1, 2, 3].iter().map(|&x| x.to_string()).collect::<Vec<String>>();

// WRONG: Using .map() for side effects (wasteful allocation if collected)
let results: Vec<()> = items.iter().map(|item| process(item)).collect();

// CORRECT: Use .for_each() for side effects
items.iter().for_each(|item| process(item));
```

## Gotchas
- On arrays, `iter()` (in Rust editions < 2021) yields `&T`; on `Vec`, `into_iter()` yields `T` directly — this was unified in Edition 2021 but remains a common confusion
- `.zip()` stops at the shorter iterator — silent truncation, no warning
- `.chain()` requires both iterators to yield the same item type — may need `.copied()` or `.cloned()` to align
- `.enumerate()` returns `(usize, &T)` for `.iter()` — the index is always `usize`, useful with `.find()` for position
- `.fold()` takes the accumulator as the first closure argument, the element as second — opposite of some languages (e.g., JavaScript reduce)
- `.for_each()` is eager (runs immediately); `.map()` is lazy (runs only when consumed) — using `.map()` without consuming the iterator does nothing
- `.copied()` converts `Iterator<Item=&T>` to `Iterator<Item=T>` for `Copy` types — cheaper than `.cloned()`

## Related
- rust/stdlib/iterators-closures.md
- rust/stdlib/collections.md
- rust/stdlib/string-ops.md
