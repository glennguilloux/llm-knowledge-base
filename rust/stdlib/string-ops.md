---
id: "rust-stdlib-string-ops"
title: "Rust String Operations — Concatenation, Splitting, Trimming, Replacing"
language: "rust"
category: "stdlib"
subcategory: "text"
tags: ["rust", "string", "concatenation", "split", "trim", "replace", "regex"]
version: "1.75+"
retrieval_hint: "Rust string concat push_str format split trim replace regex crate contains"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust String Operations — Concatenation, Splitting, Trimming, Replacing

## When to Use
- `+` operator for combining an owned `String` with a `&str` (consumes left operand)
- `format!` for building strings from many parts without ownership concerns
- `push_str()` for efficient in-place appends to a `String`
- `split()` / `split_whitespace()` for parsing delimited text
- `trim()` / `trim_matches()` for stripping whitespace or specific characters
- `replace()` for find-and-replace on owned strings
- `regex` crate for complex pattern matching beyond simple string/char patterns

## Standard Pattern

```rust
// --- Concatenation: + operator (consumes left-hand String) ---
fn concat_plus() -> String {
    let mut full = String::from("hello");
    full = full + " " + "world"; // `full` consumed, reassigned
    full
}

// --- Concatenation: format! (no consumption, clean multi-part) ---
fn concat_format(a: &str, b: &str, n: i32) -> String {
    format!("{} {} — count: {}", a, b, n)
}

// --- Concatenation: push_str (efficient in-place append) ---
fn build_csv(values: &[&str]) -> String {
    let mut result = String::new();
    for (i, v) in values.iter().enumerate() {
        if i > 0 {
            result.push_str(", ");
        }
        result.push_str(v);
    }
    result
}

// --- Splitting ---
fn parse_headers(line: &str) -> Vec<&str> {
    line.split(',').map(|s| s.trim()).collect()
}

fn tokenize(text: &str) -> Vec<&str> {
    text.split_whitespace().collect()
}

// --- Trimming ---
fn clean_input(input: &str) -> &str {
    input.trim() // Strips leading/trailing whitespace
}

// --- Replacing ---
fn sanitize(input: &str) -> String {
    input.replace("foo", "bar") // Returns new String
}

// --- contains ---
fn has_extension(filename: &str, ext: &str) -> bool {
    filename.contains(ext)
}

// --- Regex (requires regex crate: cargo add regex) ---
use regex::Regex;

fn extract_emails(text: &str) -> Vec<String> {
    let re = Regex::new(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}").unwrap();
    re.find_iter(text)
        .map(|m| m.as_str().to_string())
        .collect()
}

fn main() {
    println!("{}", concat_plus());
    println!("{}", concat_format("hello", "world", 42));

    let csv = build_csv(&["one", "two", "three"]);
    println!("csv: {}", csv);

    let headers = parse_headers("name, age, email");
    println!("{:?}", headers);

    let tokens = tokenize("  hello   world  ");
    println!("{:?}", tokens);

    println!("clean: '{}'", clean_input("  hello  "));
    println!("sanitized: {}", sanitize("foo bar foo"));

    let emails = extract_emails("Contact alice@example.com or bob@test.org");
    println!("emails: {:?}", emails);
}
```

## Common Mistakes

```rust
// WRONG: Using format! inside a tight loop when push_str is faster
fn build_slow(lines: &[&str]) -> String {
    let mut result = String::new();
    for line in lines {
        result = format!("{}{}\n", result, line); // Re-allocates entire string each iteration
    }
    result
}

// CORRECT: Use push_str or write! for accumulation
fn build_fast(lines: &[&str]) -> String {
    let mut result = String::new();
    for line in lines {
        result.push_str(line);
        result.push('\n');
    }
    result
}

// WRONG: Forgetting that + consumes the left operand
let mut s = String::from("hello");
s = s + " there"; // Works — we reassigned
let s2 = s + " again"; // s is consumed, s2 is "hello there again"
// println!("{}", s); // COMPILE ERROR: s was moved

// CORRECT: Use format! if you need both the original and the combined string
let s = String::from("hello");
let combined = format!("{} there", s);
println!("original: {}", s);      // Still valid
println!("combined: {}", combined);

// WRONG: Using replace() and discarding the result (strings are immutable)
let mut name = String::from("hello world");
name.replace("hello", "hi"); // Returns a new String — original unchanged!
assert_eq!(name, "hello world"); // replace() didn't mutate!

// CORRECT: Assign the result back
let mut name = String::from("hello world");
name = name.replace("hello", "hi");
assert_eq!(name, "hi world");

// WRONG: Pattern too broad in trim_matches — trimming individual chars not a sequence
let s = "www.example.com";
let trimmed = s.trim_matches('w'); // Trims individual 'w' chars, not "www"
println!("{}", trimmed); // ".example.com" — but also trims trailing coincidental chars

// CORRECT: Use strip_prefix/strip_suffix for known prefixes/suffixes
let s = "www.example.com";
let trimmed = s.strip_prefix("www.").unwrap_or(s);
println!("{}", trimmed); // "example.com"
```

## Gotchas
- The `+` operator signature is `fn add(self, rhs: &str) -> String` — it **consumes** the left-hand `String`
- `split()` returns an iterator of `&str` slices borrowing from the original string — lifetime tied to source
- `replace()` always returns a new `String`; it never mutates in place (Rust strings are not mutable via methods returning `String`)
- `regex::Regex::new()` returns a `Result` — compile-time errors (bad regex), so use `unwrap()` or `expect()` at startup, not per-call
- Creating a `Regex` is expensive — compile once with `lazy_static` or `once_cell`, reuse many times
- `contains(char)` and `contains(&str)` both work but with different performance — char contains is a single byte scan
- `trim()` only strips ASCII whitespace and `\u{0085}`; does NOT strip all Unicode whitespace — use `trim_matches` with a custom closure for full Unicode

## Related
- rust/stdlib/string-str.md
- rust/stdlib/iterators-closures.md
