---
id: "anti-patterns-rust-unnecessary-clone"
title: "Rust Anti-Pattern: Unnecessary Cloning"
language: "rust"
category: "anti-patterns"
tags: ["antipatterns", "rust", "clone", "ownership", "borrowing", "performance"]
version: "n/a"
retrieval_hint: "Rust unnecessary clone borrow checker performance impact borrowing patterns when to clone"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust Anti-Pattern: Unnecessary Cloning

## When to Use
- Reviewing Rust code for performance issues
- Training LLMs to write idiomatic Rust with proper ownership
- Refactoring code that overuses `.clone()` to silence the borrow checker
- Understanding when cloning is genuinely necessary vs. when borrowing suffices

## Standard Pattern

```rust
// WRONG: Cloning to silence the borrow checker
fn greet(name: String) {
    println!("Hello, {}", name.clone());
    println!("Goodbye, {}", name);
}
// Clone is pointless — println! borrows, doesn't consume

// CORRECT: Borrow with &str
fn greet(name: &str) {
    println!("Hello, {}", name);
    println!("Goodbye, {}", name);
}

// WRONG: Cloning a String just to pass to a function that borrows
let name = String::from("Alice");
let upper = name.clone().to_uppercase();  // Unnecessary clone
println!("{}", name);

// CORRECT: to_uppercase() creates a new String, doesn't need ownership
let name = String::from("Alice");
let upper = name.to_uppercase();
println!("{}", name);

// WRONG: Vec clone in function parameters
fn process(items: Vec<String>) {
    for item in &items {
        println!("{}", item);
    }
}
let data = vec!["a".into(), "b".into()];
process(data.clone());  // Heap allocation just to pass a reference

// CORRECT: Borrow the slice
fn process(items: &[String]) {
    for item in items {
        println!("{}", item);
    }
}
let data = vec!["a".into(), "b".into()];
process(&data);

// WRONG: Cloning in a loop
let mut results = Vec::new();
for item in &items {
    results.push(item.clone());  // Clones every element
}

// CORRECT: Use to_owned() or into_iter() when consuming
for item in &items {
    results.push(item.to_owned());  // Same cost, clearer intent
}
// Or if items are no longer needed:
for item in items {
    results.push(item);  // Zero-cost move
}

// WRONG: Box clone for trait objects
let handler: Box<dyn Handler> = Box::new(MyHandler);
let copy = handler.clone();  // Requires Clone on dyn Handler

// CORRECT: Use Rc/Arc for shared ownership
use std::rc::Rc;
let handler: Rc<dyn Handler> = Rc::new(MyHandler);
let shared = Rc::clone(&handler);  // Reference count bump, no data copy

// WRONG: String where &str suffices
fn is_valid(input: String) -> bool {  // Takes ownership unnecessarily
    input.len() > 0
}

// CORRECT: Borrow with &str
fn is_valid(input: &str) -> bool {
    !input.is_empty()
}

// WRONG: HashMap clone to avoid borrow checker
let config = load_config();
let value = config.get("key").cloned().unwrap_or_default();
// clone() here is fine — cloned() on Option is idiomatic

// CORRECT: Cow for conditional ownership
use std::borrow::Cow;

fn process(input: Cow<str>) -> Cow<str> {
    if input.contains("bad") {
        Cow::Owned(input.replace("bad", "good"))  // Allocates only when needed
    } else {
        input  // Zero allocation
    }
}
let borrowed = process(Cow::Borrowed("hello"));  // No allocation
let owned = process(Cow::Borrowed("bad word"));   // Allocates
```

## Common Mistakes
The most common Rust anti-pattern is sprinkling `.clone()` everywhere to satisfy the borrow checker, turning Rust's zero-cost abstractions into hidden heap allocations. Each `String::clone()` copies the entire heap buffer; each `Vec::clone()` copies all elements. Developers new to Rust add clones out of frustration with ownership errors, but this defeats Rust's core performance advantage. The fix is to prefer borrowing (`&T`, `&str`, `&[T]`) in function parameters and use `Cow<'_, T>` when ownership is sometimes needed. Cloning is genuinely necessary for shared ownership across threads (`Arc`), owned values in collections that outlive their source, or when an API requires owned data.

## Gotchas
- `clone()` on `String`, `Vec`, `HashMap` copies heap data — it is NOT free
- `to_owned()` and `clone()` are equivalent for `String`/`Vec` but `to_owned()` communicates intent better for `&str -> String`
- `Rc::clone(&rc)` only bumps a reference count — it's cheap and idiomatic
- `Arc::clone(&arc)` is the thread-safe equivalent — also cheap
- `Cow<'a, T>` avoids cloning when the data is borrowed and only allocates when modification is needed
- `&str` parameters accept both `&String` (auto-deref) and `&str` — use `&str` for maximum flexibility
- `as_str()` converts `&String` to `&str` for free; use it instead of `.clone()`
- `#[derive(Clone)]` on large structs makes accidental deep copies easy — be deliberate
- Clippy warns about unnecessary clones with `clippy::redundant_clone` — enable it in CI
- `clone_from()` reuses existing allocation when possible and is more efficient than `x = y.clone()`

## Related
- rust/testing/mocking.md
- rust/web/axum-state-error.md
- anti-patterns/rust-antipatterns.md
