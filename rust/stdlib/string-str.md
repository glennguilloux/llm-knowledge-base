---
id: "rust-stdlib-string-str"
title: "Rust String vs &str — Ownership, Borrowing, and Construction"
language: "rust"
category: "stdlib"
subcategory: "text"
tags: ["rust", "string", "str", "borrowing", "ownership", "format", "to_string"]
version: "1.75+"
retrieval_hint: "Rust String vs &str when to use to_string to_owned borrowing format macro"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust String vs &str — Ownership, Borrowing, and Construction

## When to Use
- `&str` for read-only string views (function parameters, literals, slices)
- `String` for owned, mutable, growable strings (building, returning, storing)
- `format!` macro for constructing strings from multiple parts
- `to_string()` or `to_owned()` to convert `&str` → `String` when ownership is needed
- Prefer `&str` in function signatures to accept both `String` and string literals

## Standard Pattern

```rust
// --- Function signatures: prefer &str for input, return String for output ---
fn greet(name: &str) -> String {
    format!("Hello, {}!", name)
}

// --- Converting &str to String ---
fn build_message(label: &str, count: usize) -> String {
    // format! returns String directly
    format!("{} has {} items", label, count)
}

// --- to_string() vs to_owned(): both produce String ---
fn demo_conversions() {
    let literal: &str = "hello";
    let owned_a: String = literal.to_string();   // Via Display trait
    let owned_b: String = literal.to_owned();    // Via Clone trait — same result

    assert_eq!(owned_a, owned_b); // Both are "hello"
}

// --- Borrowing a String as &str ---
fn print_slice(s: &str) {
    println!("slice: {}", s);
}

fn demo_borrowing() {
    let owned = String::from("hello world");
    print_slice(&owned);                    // &String auto-coerces to &str
    print_slice(&owned[0..5]);             // Slicing produces &str

    // Can have many shared &str borrows at once
    let ref1: &str = &owned;
    let ref2: &str = &owned;
    println!("{} {}", ref1, ref2);          // Both valid — shared borrow
}

// --- Modifying strings requires mut String ---
fn capitalize_push(s: &mut String) {
    if let Some(first) = s.get(0..1) {
        s.replace_range(0..1, &first.to_uppercase());
    }
}

fn main() {
    let msg = greet("world");
    println!("{}", msg);

    let mut buffer = String::from("hello");
    capitalize_push(&mut buffer);
    println!("{}", buffer); // "Hello"

    demo_conversions();
    demo_borrowing();
}
```

## Common Mistakes

```rust
// WRONG: Returning &str pointing to local String (dangling reference)
fn broken_label() -> &str {
    let s = String::from("temp");
    &s // ERROR: `s` is dropped here, returned reference would dangle
}

// CORRECT: Return String (owned)
fn working_label() -> String {
    let s = String::from("temp");
    s // Ownership moved out — valid
}

// WRONG: Using .to_string() on a String (no-op, confuses readers)
let name = String::from("Alice");
let redundant: String = name.to_string(); // Works but wasteful

// CORRECT: Just use it directly — or if you need a new clone, use .clone()
let name = String::from("Alice");
let copy: String = name.clone(); // Clear intent

// WRONG: Passing String where &str works (forces caller to own)
fn takes_string(s: String) {
    println!("{}", s);
}
fn caller() {
    takes_string("hello".to_string()); // Unnecessary allocation
}

// CORRECT: Accept &str — works with both String and literals
fn takes_str(s: &str) {
    println!("{}", s);
}
fn caller() {
    takes_str(&String::from("hello")); // Auto-deref coercion
    takes_str("hello");                // Works with literals too
}

// WRONG: Trying to mutate a &str reference directly
fn bad_append(s: &str) -> String {
    s + " world" // Can't modify &str; + creates new String, not mutation
}

// CORRECT: Use push_str on a mutable String, or + operator for new String
fn good_append(s: &str) -> String {
    let mut result = String::from(s);
    result.push_str(" world");
    result
}
// Or simply: format!("{} world", s)
```

## Gotchas
- `String` coerces to `&str` via `Deref<Target=str>` — `&String` automatically becomes `&str` when needed
- `to_string()` and `to_owned()` produce identical results for `&str`; `to_string()` uses the `Display` trait while `to_owned()` uses `Clone`
- String literals (`"..."`) are `&'static str` — they live for the entire program duration
- `format!` returns a `String`, not a `&str` — this is the go-to way to build strings from parts
- Slicing a `String` with `&s[start..end]` operates on **bytes**, not characters — slicing mid-`char` panics at runtime
- You cannot iterate over a `String` directly with `for c in s` — use `s.chars()` for Unicode characters or `s.bytes()` for raw bytes
- `&str` is an immutable fat pointer (pointer + length); `String` owns a heap-allocated buffer with capacity

## Related
- rust/stdlib/string-ops.md
- rust/stdlib/ownership.md
- rust/stdlib/iterators-closures.md
