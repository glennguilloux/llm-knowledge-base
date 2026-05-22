---
id: "rust-stdlib-result-option"
title: "Result and Option Patterns"
language: "rust"
category: "stdlib"
tags: ["result", "option", "error-handling", "unwrap", "question-mark", "combinators"]
version: "1.75+"
retrieval_hint: "Result Option unwrap ? operator map and_then error handling"
last_verified: "2026-05-22"
confidence: "high"
---

# Result and Option Patterns

## When to Use
- Handling operations that can fail (file I/O, network, parsing)
- Representing optional values without null pointers
- Chaining fallible operations cleanly
- Building robust error recovery logic

## Standard Pattern

```rust
use std::num::ParseIntError;
use std::fs;

// Basic Result usage with ? operator
fn read_count(path: &str) -> Result<i32, Box<dyn std::error::Error>> {
    let content = fs::read_to_string(path)?;
    let count: i32 = content.trim().parse()?;
    Ok(count)
}

// Option for optional values
fn find_user(users: &[User], id: u64) -> Option<&User> {
    users.iter().find(|u| u.id == id)
}

// Chaining with map, and_then, unwrap_or
fn parse_port(s: Option<&str>) -> u16 {
    s.and_then(|s| s.parse::<u16>().ok())
        .unwrap_or(8080)
}

// Combining Result and Option
fn get_env_port() -> Result<u16, std::env::VarError> {
    let val = std::env::var("PORT")?;
    val.parse::<u16>()
        .map_err(|e| std::env::VarError::NotPresent) // simplified
}

// Option combinators
fn process_name(input: Option<&str>) -> String {
    input
        .map(|s| s.trim())
        .filter(|s| !s.is_empty())
        .map(|s| s.to_uppercase())
        .unwrap_or_else(|| "UNKNOWN".to_string())
}

// Result combinators
fn double_parse(s: &str) -> Result<i64, String> {
    s.parse::<i32>()
        .map(|n| n as i64 * 2)
        .map_err(|e| format!("Parse error: {}", e))
}

struct User {
    id: u64,
    name: String,
    email: Option<String>,
}

impl User {
    fn display_email(&self) -> &str {
        self.email.as_deref().unwrap_or("no email")
    }
}

fn main() {
    let port = parse_port(Some("3000"));
    println!("Port: {}", port);

    let name = process_name(Some("  alice  "));
    println!("{}", name); // "ALICE"

    let users = vec![
        User { id: 1, name: "Alice".into(), email: Some("a@b.com".into()) },
        User { id: 2, name: "Bob".into(), email: None },
    ];
    for user in &users {
        println!("{}: {}", user.name, user.display_email());
    }
}
```

## Common Mistakes

```rust
// WRONG: unwrap() everywhere — panics on None/Err
fn get_port() -> u16 {
    std::env::var("PORT").unwrap().parse::<u16>().unwrap()
}

// CORRECT: Use ? or provide defaults
fn get_port() -> u16 {
    std::env::var("PORT")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(8080)
}

// WRONG: Matching when combinators suffice
fn get_length(maybe: Option<String>) -> usize {
    match maybe {
        Some(s) => s.len(),
        None => 0,
    }
}

// CORRECT: Use map_or
fn get_length(maybe: Option<String>) -> usize {
    maybe.map_or(0, |s| s.len())
}

// WRONG: if let Some(x) = option { return x; } else { return default; }
fn get_value(opt: Option<i32>) -> i32 {
    if let Some(v) = opt {
        v
    } else {
        0
    }
}

// CORRECT: unwrap_or / unwrap_or_else
fn get_value(opt: Option<i32>) -> i32 {
    opt.unwrap_or(0)
}

// WRONG: Converting Option to Result without context
fn find_item(id: u32) -> Result<Item, String> {
    lookup(id).ok_or("not found".into()) // generic error
}

// CORRECT: Provide meaningful error context
fn find_item(id: u32) -> Result<Item, String> {
    lookup(id).ok_or_else(|| format!("Item {} not found in database", id))
}

// WRONG: Using is_some() + unwrap() instead of if let
let opt = Some(42);
if opt.is_some() {
    println!("{}", opt.unwrap()); // double work
}

// CORRECT: Pattern match
if let Some(val) = opt {
    println!("{}", val);
}
```

## Gotchas
- `unwrap()` panics in debug AND release — use `expect()` with a message if you must unwrap
- `?` operator auto-converts errors via `From` trait — implement `From` for custom error types
- `Option::ok_or` / `Result::ok` convert between Option and Result
- `transpose()` converts `Option<Result<T,E>>` to `Result<Option<T>, E>` and vice versa
- `and_then` chains operations that return Option/Result; `map` transforms the inner value
- `unwrap_or` evaluates the default eagerly; `unwrap_or_else` is lazy — prefer the latter for expensive defaults
- `as_ref()` converts `&Option<T>` to `Option<&T>` — useful to avoid moving out of an Option

## Related
- rust/stdlib/error-handling.md
- rust/stdlib/ownership.md
- rust/stdlib/traits.md
