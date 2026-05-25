---
id: "rust-stdlib-ownership"
title: "Ownership and Borrowing"
language: "rust"
category: "stdlib"
tags: ["ownership", "borrowing", "lifetime", "move", "reference", "memory"]
version: "1.75+"
retrieval_hint: "ownership borrowing move semantics lifetime reference String &str"
last_verified: "2026-05-24"
confidence: "high"
---

# Ownership and Borrowing

## When to Use
- Managing heap-allocated data (String, Vec, Box)
- Passing data between functions without unnecessary copying
- Sharing data across threads safely
- Designing APIs that enforce correct memory usage at compile time

## Standard Pattern

```rust
use std::collections::HashMap;

// Ownership: each value has exactly one owner
fn process_data(data: String) -> String {
    // `data` is owned by this function now
    format!("processed: {}", data)
} // `data` is dropped here if not returned

// Borrowing: immutable references (&T)
fn calculate_length(s: &str) -> usize {
    s.len() // can read but not modify
}

// Mutable borrowing (&mut T)
fn append_greeting(s: &mut String) {
    s.push_str(", world!");
}

// Returning owned data with ownership transfer
fn build_config(key: &str, value: &str) -> HashMap<String, String> {
    let mut config = HashMap::new();
    config.insert(key.to_string(), value.to_string());
    config
}

// Structs own their data
struct User {
    name: String,
    email: String,
}

impl User {
    // Takes owned strings — caller decides whether to clone
    fn new(name: String, email: String) -> Self {
        Self { name, email }
    }

    // Borrows self, returns borrowed slice
    fn display_name(&self) -> &str {
        if self.name.is_empty() {
            "Anonymous"
        } else {
            &self.name
        }
    }

    // Mutable borrow to modify in place
    fn update_email(&mut self, new_email: String) {
        self.email = new_email;
    }
}

fn main() {
    let s = String::from("hello");
    let processed = process_data(s);
    // s is no longer valid here — ownership moved

    let name = String::from("Alice");
    let len = calculate_length(&name);
    // name is still valid — only borrowed
    println!("{} has length {}", name, len);

    let mut greeting = String::from("Hello");
    append_greeting(&mut greeting);
    println!("{}", greeting); // "Hello, world!"

    let mut user = User::new("Alice".into(), "alice@example.com".into());
    user.update_email("new@example.com".into());
    println!("{}", user.display_name());
}
```

## Common Mistakes

```rust
// WRONG: Using a value after it's been moved
fn main() {
    let s = String::from("hello");
    let s2 = s;
    println!("{}", s); // ERROR: value borrowed after move
}

// CORRECT: Clone if you need both copies
fn main() {
    let s = String::from("hello");
    let s2 = s.clone();
    println!("{}, {}", s, s2); // Both valid
}

// WRONG: Multiple mutable references
fn main() {
    let mut s = String::from("hello");
    let r1 = &mut s;
    let r2 = &mut s; // ERROR: cannot borrow as mutable twice
    println!("{}, {}", r1, r2);
}

// CORRECT: Scope the mutable borrow
fn main() {
    let mut s = String::from("hello");
    {
        let r1 = &mut s;
        r1.push_str(" world");
    } // r1 goes out of scope
    let r2 = &mut s; // Now this is fine
    println!("{}", r2);
}

// WRONG: Taking &String when &str suffices
fn greet(name: &String) {
    println!("Hello, {}!", name);
}

// CORRECT: Accept &str — works for both String and &str
fn greet(name: &str) {
    println!("Hello, {}!", name);
}

// WRONG: Returning a reference to a local variable
fn dangling() -> &str {
    let s = String::from("hello");
    &s // ERROR: s is dropped, reference would dangle
}

// CORRECT: Return an owned value
fn not_dangling() -> String {
    String::from("hello")
}
```

## Gotchas
- `String` is owned (heap-allocated, mutable); `&str` is a borrowed string slice (immutable view)
- `Copy` types (i32, f64, bool) are copied on assignment, not moved — no ownership issues
- `Clone` is explicit deep copy — use when you genuinely need duplicate data
- `mem::take` and `mem::replace` let you move data out of a mutable reference without dropping
- Lifetimes are about ensuring references don't outlive the data they point to
- `&mut` and `&` cannot coexist in the same scope (except with `RefCell`)
- Returning references requires matching lifetime annotations — the compiler will tell you

## Related
- rust/stdlib/lifetimes.md
- rust/stdlib/result-option.md
- rust/stdlib/traits.md
