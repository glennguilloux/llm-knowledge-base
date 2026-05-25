---
id: "rust-stdlib-lifetimes"
title: "Lifetime Basics"
language: "rust"
category: "stdlib"
tags: ["lifetime", "borrow", "reference", "elision", "static"]
version: "1.75+"
retrieval_hint: "lifetime annotation elision static borrow reference dangling"
last_verified: "2026-05-24"
confidence: "high"
---

# Lifetime Basics

## When to Use
- Functions that return references to borrowed data
- Structs that hold references to external data
- Resolving compiler errors about borrowed data outliving its source
- Understanding why the compiler rejects certain reference patterns

## Standard Pattern

```rust
// Lifetime annotations tell the compiler how long references are valid
// 'a reads as "lifetime a" — it's a constraint, not a duration

// Function with lifetime parameter
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

// Struct holding a reference — must annotate lifetime
struct Excerpt<'a> {
    text: &'a str,
}

impl<'a> Excerpt<'a> {
    fn level(&self) -> i32 {
        3
    }

    // Lifetime elision: compiler infers lifetimes here
    fn announce(&self, announcement: &str) -> &str {
        println!("Attention: {}", announcement);
        self.text
    }
}

// Multiple lifetime parameters
fn first_sentence<'a, 'b>(text: &'a str, _default: &'b str) -> &'a str {
    match text.find('.') {
        Some(i) => &text[..=i],
        None => text,
    }
}

// 'static — lives for the entire program
fn static_str() -> &'static str {
    "I live forever" // string literals are 'static
}

// Lifetime elision rules (compiler auto-infers):
// 1. Each input reference gets its own lifetime
// 2. If exactly one input lifetime, output gets that lifetime
// 3. If &self or &mut self, output gets self's lifetime

// These are equivalent:
fn first_word(s: &str) -> &str { /* ... */ }
fn first_word_explicit<'a>(s: &'a str) -> &'a str { /* ... */ }

fn main() {
    let string1 = String::from("long string");
    let result;
    {
        let string2 = String::from("xyz");
        result = longest(string1.as_str(), string2.as_str());
        println!("Longest: {}", result);
    }
    // result cannot be used here — string2 is dropped

    let novel = "Call me Ishmael. Some years ago...";
    let excerpt = Excerpt {
        text: &novel[..15],
    };
    println!("{}", excerpt.text);
}
```

## Common Mistakes

```rust
// WRONG: Returning a reference to a local variable
fn bad_function() -> &str {
    let s = String::from("hello");
    &s // ERROR: s dropped, reference dangles
}

// CORRECT: Return owned data
fn good_function() -> String {
    String::from("hello")
}

// WRONG: Missing lifetime annotation on return
fn longest(x: &str, y: &str) -> &str {
    if x.len() > y.len() { x } else { y }
}
// ERROR: compiler can't infer which input the output borrows from

// CORRECT: Annotate lifetimes
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

// WRONG: Trying to store a temporary in a struct
struct Holder {
    data: &str, // ERROR: missing lifetime specifier
}

// CORRECT: Annotate the struct
struct Holder<'a> {
    data: &'a str,
}

// WRONG: Returning a reference with a shorter lifetime than the input
fn trim_and_return(s: &str) -> &str {
    let trimmed = s.trim(); // trimmed borrows from s
    let local = String::from(trimmed);
    &local // ERROR: local dropped at end of function
}

// CORRECT: Return owned data when creating new strings
fn trim_and_return(s: &str) -> String {
    s.trim().to_string()
}
```

## Gotchas
- Lifetimes are NOT about how long data lives — they're about how long references to data are valid
- The borrow checker works at compile time — zero runtime cost
- `'static` does NOT mean "lives forever" — it means "can live for the entire program"
- String literals are `&'static str` because they're baked into the binary
- Lifetime elision covers ~90% of cases — you rarely need explicit annotations
- `&'a mut &'b mut T` requires `'a: 'b` (outlives relationship)
- Functions returning references to multiple inputs usually need multiple lifetime params
- `Box<dyn Trait>` has an implicit `'static` bound — use `Box<dyn Trait + 'a>` for non-static

## Related
- rust/stdlib/ownership.md
- rust/stdlib/traits.md
- rust/stdlib/result-option.md
