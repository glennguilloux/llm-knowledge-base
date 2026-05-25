---
id: "rust-stdlib-closures-capturing"
title: "Rust Closures: Capturing, Traits (Fn/FnMut/FnOnce), and Returning Closures"
language: "rust"
category: "stdlib"
subcategory: "functional"
tags: ["rust", "closure", "fn", "fnmut", "fnonce", "move", "capture", "trait-object"]
version: "1.75+"
retrieval_hint: "Rust closure Fn FnMut FnOnce move capture returning closure Box dyn Fn"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust Closures: Capturing, Traits (Fn/FnMut/FnOnce), and Returning Closures

## When to Use

- Closures as arguments to higher-order functions (`sort_by_key`, `map_with`, callbacks)
- `Fn`: closure only reads captured environment (can be called multiple times concurrently)
- `FnMut`: closure mutates captured environment (needs `&mut` to call, exclusive)
- `FnOnce`: closure consumes captured environment (can only be called once)
- `move` closures: forcing ownership transfer into the closure (threads, `'static` lifetimes)
- `Box<dyn Fn(...)>`: returning closures from functions when type is not known at compile time

Quick decision tree:
```text
Does the closure only read captured variables?           -> Fn
Does it mutate captured variables?                        -> FnMut
Does it move/consume captured variables (or is called once)? -> FnOnce
Need to return a closure or store in a struct?            -> Box<dyn Fn(...)> or impl Fn(...)
Need a 'static closure (e.g., for threads)?              -> move || { ... }
```

## Standard Pattern

```rust
use std::collections::HashMap;

// --- Fn: read-only capture ---
fn apply_twice<F>(x: i32, f: F) -> i32
where
    F: Fn(i32) -> i32,
{
    f(f(x))
}

let multiplier = 3;
// Closure captures `multiplier` by shared reference (Fn)
let result = apply_twice(5, |x| x * multiplier);
assert_eq!(result, 45); // 5 * 3 * 3


// --- FnMut: mutating capture ---
fn apply_repeatedly<F>(x: &mut i32, mut f: F)
where
    F: FnMut(i32) -> i32,
{
    for _ in 0..3 {
        *x = f(*x);
    }
}

let mut count = 0;
let mut val = 1;
apply_repeatedly(&mut val, |x| {
    count += 1;              // Mutates captured `count`
    x * 2
});
assert_eq!(val, 8);   // 1 -> 2 -> 4 -> 8
assert_eq!(count, 3); // Closure was called 3 times


// --- FnOnce: consuming capture ---
fn run_once<F>(f: F) -> String
where
    F: FnOnce() -> String,
{
    f()
}

let data = vec![1, 2, 3];
// Closure consumes `data` by moving it in — can only be called once
let result = run_once(move || format!("{:?}", data));
// `data` is no longer accessible here
assert_eq!(result, "[1, 2, 3]");


// --- move closures for threads ---
fn spawn_worker(items: Vec<i32>) -> std::thread::JoinHandle<i32> {
    // `items` must be moved into the closure for 'static lifetime
    std::thread::spawn(move || {
        items.into_iter().sum()
    })
    // `items` moved into the thread — no longer valid in this scope
}


// --- Returning closures with Box<dyn Fn> ---
fn make_adder(x: i32) -> Box<dyn Fn(i32) -> i32> {
    Box::new(move |y| x + y)
}

let add5 = make_adder(5);
assert_eq!(add5(10), 15);
assert_eq!(add5(20), 25);


// --- impl Fn return type (zero-cost, no heap allocation) ---
fn make_multiplier(factor: i32) -> impl Fn(i32) -> i32 {
    move |x| x * factor
}

let triple = make_multiplier(3);
assert_eq!(triple(7), 21);


// --- Storing closures in a struct ---
struct Validator<F>
where
    F: Fn(&str) -> bool,
{
    check: F,
}

impl<F> Validator<F>
where
    F: Fn(&str) -> bool,
{
    fn new(check: F) -> Self {
        Validator { check }
    }

    fn is_valid(&self, input: &str) -> bool {
        (self.check)(input)
    }
}

let non_empty = Validator::new(|s: &str| !s.is_empty());
assert!(non_empty.is_valid("hello"));
assert!(!non_empty.is_valid(""));


// --- Closure trait hierarchy: Fn : FnMut : FnOnce ---
fn demonstrate_hierarchy() {
    let s = String::from("hello");

    // FnOnce: consumes s
    let consume = move || s;
    consume();
    // consume(); // ERROR: s already moved

    // FnMut: mutates captured ref
    let mut total = 0u32;
    let mut accumulate = |x: u32| { total += x; };
    accumulate(5);
    accumulate(10);
    assert_eq!(total, 15);

    // Fn: only reads
    let name = String::from("world");
    let greet = || println!("hello {}", name);
    greet();
    greet(); // Can call multiple times
    drop(name); // `name` is still alive after greet()
}
```

## Common Mistakes

```rust
// WRONG: Assuming closures always impl Fn — some are FnOnly
let data = vec![1, 2, 3];
let consume = || data; // This is FnOnce because it moves `data`
// let result = consume();
// let result2 = consume(); // ERROR: called more than once

// CORRECT: Use move only when needed, and accept FnOnce in generic bounds
fn run_it(f: impl FnOnce() -> i32) -> i32 { f() }


// WRONG: Returning a closure that borrows local variables (dangling reference)
fn bad_closure() -> impl Fn(i32) -> i32 {
    let offset = 10;
    |x| x + offset // ERROR: offset is a local variable, closure would outlive it
}

// CORRECT: Use move to capture by value, or use impl Fn with move
fn good_closure() -> impl Fn(i32) -> i32 {
    let offset = 10;
    move |x| x + offset // offset is moved into the closure
}


// WRONG: Using FnMut bound when closure consumes captured value once
let name = String::from("Rust");
let printer = |label: &str| {
    let owned = name; // Moves `name` — this is FnOnce
    println!("{}: {}", label, owned);
};

// Calls:
// printer("a"); // If it compiled, this would work
// printer("b"); // But this would fail — name already moved

// CORRECT: Accept FnOnce when the closure consumes its environment
fn call_once(f: impl FnOnce() + 'static) {
    f();
}


// WRONG: Forgetting that move closures move ALL captured variables
let expensive = vec![1; 1_000_000];
let cheap = 42i32;
// The `move` keyword moves ALL captures, including `cheap` and `expensive`
let closure = move || {
    println!("{} {}", cheap, expensive.len());
};
// `expensive` is gone — might not have intended that

// CORRECT: Only move what's needed; clone cheap values before move
let expensive = vec![1; 1_000_000];
let cheap = 42i32;
let expensive_clone = expensive.clone();
let closure = move || {
    println!("{} {}", cheap, expensive_clone.len());
};
// `expensive` still available here (unless explicitly used in move)


// WRONG: Box<dyn Fn> without specifying Send when needed across threads
fn bad_spawn() {
    let data = vec![1, 2, 3];
    // std::thread::spawn(|| println!("{:?}", data)); // ERROR: not 'static
    // Box<dyn Fn() + 'static> is also insufficient without Send
}

// CORRECT: Box<dyn Fn() + Send + 'static> for thread-spawned closures
fn good_spawn() -> std::thread::JoinHandle<()> {
    let data = vec![1, 2, 3];
    std::thread::spawn(move || println!("{:?}", data))
}
```

## Gotchas
- Every closure automatically implements one or more of `Fn`, `FnMut`, `FnOnce` — the compiler picks the most restrictive one; `Fn` is a subtrait of `FnMut` which is a subtrait of `FnOnce`
- `move || { ... }` captures variables by **value** (move), even if the body only reads them — this forces a transfer of ownership
- When a closure captures a variable by mutable reference (`FnMut`), the closure itself must be declared `mut` to call it: `let mut f = || { ... }; f();`
- `impl Fn(i32) -> i32` as a return type is monomorphized (zero-cost) but the caller cannot choose the closure type; `Box<dyn Fn(i32) -> i32>` allows dynamic dispatch but incurs heap allocation and vtable costs
- A closure that only reads captured variables may still be `FnOnce` if it moves a captured value out of the body — the compiler determines the trait based on how captures are **used**, not just whether they're `move`
- Closures cannot name their own types — you must use `impl Fn(...)` or `Box<dyn Fn(...)>` to pass them around
- `fn` items (not closures, but function pointers) implement all three Fn traits and can be used wherever closures are expected — but they cannot capture any environment

## Related
- rust/stdlib/iterators-closures.md
- rust/stdlib/ownership.md
- rust/stdlib/traits.md
