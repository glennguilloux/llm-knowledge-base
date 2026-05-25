---
id: "rust-stdlib-numeric-conversion"
title: "Rust Numeric Conversions — parse, to_string, From/TryFrom, Error Handling"
language: "rust"
category: "stdlib"
subcategory: "conversion"
tags: ["rust", "parse", "to_string", "from", "tryfrom", "conversion", "numeric"]
version: "1.75+"
retrieval_hint: "Rust string to int parse to_string f64 to i32 From TryFrom conversion error handling"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust Numeric Conversions — parse, to_string, From/TryFrom, Error Handling

## When to Use
- `str::parse::<T>()` to convert `&str` → numeric type (returns `Result`)
- `.to_string()` on any numeric type to get a `String`
- `as` keyword for lossy but infallible casts between primitive numeric types
- `From<T>` trait for infallible conversions (e.g., `i32` → `i64`)
- `TryFrom<T>` trait for fallible conversions (e.g., `i64` → `i32`, `f64` → `i32`)
- Always handle the `Result` from `parse()` — never `.unwrap()` on user input

## Standard Pattern

```rust
use std::convert::TryFrom;

// --- String to integer via parse ---
fn parse_port(input: &str) -> Result<u16, String> {
    input.parse::<u16>()
        .map_err(|e| format!("Invalid port '{}': {}", input, e))
}

// --- Integer to String via to_string ---
fn format_id(id: u64) -> String {
    id.to_string()
}

// --- f64 to i32 (truncation) ---
fn float_to_int(value: f64) -> i32 {
    value as i32 // Truncates toward zero — no rounding!
}

// --- Safe f64 to i32 via TryFrom ---
fn safe_float_to_int(value: f64) -> Result<i32, String> {
    i32::try_from(value as i64) // First truncate, then check bounds
        .map_err(|e| format!("Cannot convert {} to i32: {}", value, e))
}

// --- From trait: infallible conversion (i32 -> i64) ---
fn widen(value: i32) -> i64 {
    i64::from(value) // Always safe — i64 can represent all i32 values
}

// --- TryFrom trait: fallible conversion (i64 -> i32) ---
fn narrow(value: i64) -> Result<i32, String> {
    i32::try_from(value)
        .map_err(|_| format!("Value {} out of range for i32", value))
}

// --- Parsing with context ---
fn parse_config_value(input: &str) -> Result<i32, String> {
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Err("Empty input".to_string());
    }
    trimmed.parse::<i32>()
        .map_err(|e| format!("Cannot parse '{}': {}", trimmed, e))
}

fn main() {
    // parse: String -> number
    match parse_port("8080") {
        Ok(port) => println!("Port: {}", port),
        Err(e) => eprintln!("Error: {}", e),
    }

    match parse_port("abc") {
        Ok(port) => println!("Port: {}", port),
        Err(e) => eprintln!("Error: {}", e), // "Invalid port 'abc': invalid digit found in string"
    }

    // to_string: number -> String
    println!("ID: {}", format_id(42));

    // f64 -> i32
    println!("3.7 as i32 = {}", float_to_int(3.7));  // 3 (truncated)
    println!("-2.9 as i32 = {}", float_to_int(-2.9)); // -2 (toward zero)

    // From: infallible
    println!("widened: {}", widen(100));

    // TryFrom: fallible
    match narrow(300) {
        Ok(v) => println!("narrowed: {}", v),
        Err(e) => eprintln!("{}", e),
    }

    match narrow(999_999_999_999) {
        Ok(v) => println!("narrowed: {}", v),
        Err(e) => eprintln!("{}", e), // Out of range
    }

    // Config parsing
    println!("{:?}", parse_config_value(" 42 "));  // Ok(42)
    println!("{:?}", parse_config_value(""));      // Err("Empty input")
    println!("{:?}", parse_config_value("abc"));   // Err("Cannot parse 'abc': ...")
}
```

## Common Mistakes

```rust
// WRONG: unwrap() on parse() with user input — panics on bad data
let port: u16 = user_input.parse().unwrap(); // Panics if input is "abc"

// CORRECT: Handle the Result properly
let port: u16 = user_input.parse().unwrap_or(8080); // Default fallback
// Or with proper error propagation:
let port: u16 = user_input.parse().map_err(|e| format!("Bad port: {}", e))?;

// WRONG: Using as for float-to-int and expecting rounding
let x: f64 = 2.7;
let n: i32 = x as i32;
println!("{}", n); // 2 — truncated, not rounded!

// CORRECT: Round explicitly if rounding is needed
let x: f64 = 2.7;
let n: i32 = x.round() as i32;
println!("{}", n); // 3

// WRONG: Using From/TryFrom interchangeably — From is infallible, TryFrom returns Result
// This won't compile: i32::from(5i64) — no From<i64> for i32
let big: i64 = 500;
let small: i32 = i32::from(big); // COMPILE ERROR

// CORRECT: Use TryFrom for potentially-lossy conversions
let big: i64 = 500;
let small: i32 = i32::try_from(big).expect("value fits in i32");

// WRONG: Parsing "42\n" without trimming — trailing newline causes parse failure
let input = "42\n";
let num: i32 = input.parse().unwrap(); // PANICS: invalid digit

// CORRECT: Trim before parsing
let input = "42\n";
let num: i32 = input.trim().parse().unwrap(); // Ok(42)

// WRONG: Assuming parse::<f64>() handles all number formats
let val = "1,000.50".parse::<f64>(); // Err — comma not valid

// CORRECT: Sanitize input or use a locale-aware parser
let cleaned = "1,000.50".replace(',', "");
let val = cleaned.parse::<f64>().unwrap(); // Ok(1000.5)
```

## Gotchas
- `as` for float-to-int **truncates toward zero** — `2.9 as i32` is `2`, `-2.9 as i32` is `-2`
- `parse::<T>()` works on any type implementing `FromStr` — integers, floats, bools, IpAddr, etc.
- `parse()` accepts leading/trailing whitespace for some types but NOT for all — always `.trim()` to be safe
- `From<T>` is infallible and reflexive — every type implements `From<T>` for itself
- `TryFrom<i64>` for `i32` returns `Err` on overflow — use it instead of `as` when input range is unknown
- `to_string()` uses the `Display` trait — for numbers it produces decimal representation, no formatting control; use `format!("{:x}", n)` for hex, `format!("{:08b}", n)` for binary
- `parse::<f64>()` accepts "inf", "NaN", "infinity" — check with `is_finite()` if you need real numbers

## Related
- rust/stdlib/string-str.md
- rust/stdlib/result-option.md
- rust/stdlib/traits.md
