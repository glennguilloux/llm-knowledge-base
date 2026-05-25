---
id: "rust-stdlib-traits"
title: "Traits and Generics"
language: "rust"
category: "stdlib"
tags: ["traits", "generics", "trait-bounds", "dyn", "associated-types", "derive"]
version: "1.75+"
retrieval_hint: "traits generics trait bounds dyn associated types derive Display Debug Clone"
last_verified: "2026-05-24"
confidence: "high"
---

# Traits and Generics

## When to Use
- Defining shared behavior across unrelated types
- Writing functions that work with multiple types (generics)
- Using trait objects for dynamic dispatch (vtable)
- Customizing standard behavior (Display, From, Iterator)

## Standard Pattern

```rust
use std::fmt;

// Define a trait
trait Summary {
    // Required method
    fn summarize(&self) -> String;

    // Default implementation
    fn preview(&self) -> String {
        format!("{}...", &self.summarize()[..20.min(self.summarize().len())])
    }
}

// Associated types — cleaner when there's a 1:1 mapping
trait Repository {
    type Item;
    type Error;

    fn find(&self, id: u64) -> Result<Self::Item, Self::Error>;
    fn save(&mut self, item: &Self::Item) -> Result<(), Self::Error>;
}

// Implementing traits
struct Article {
    title: String,
    content: String,
    author: String,
}

impl Summary for Article {
    fn summarize(&self) -> String {
        format!("{} by {}: {}", self.title, self.author, &self.content[..100.min(self.content.len())])
    }
}

// Trait bounds — monomorphized (static dispatch)
fn print_summary(item: &impl Summary) {
    println!("{}", item.summarize());
}

// Equivalent with where clause (preferred for complex bounds)
fn process<T>(item: &T) -> String
where
    T: Summary + fmt::Display,
{
    format!("Display: {} | Summary: {}", item, item.summarize())
}

// Returning impl Trait (static dispatch, one concrete type)
fn create_summary() -> impl Summary {
    Article {
        title: "Default".into(),
        content: "Default content".into(),
        author: "System".into(),
    }
}

// Trait objects — dynamic dispatch (vtable)
fn print_all(items: &[Box<dyn Summary>]) {
    for item in items {
        println!("{}", item.summarize());
    }
}

// Common derive macros
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct Point {
    x: i32,
    y: i32,
}

// From trait for conversions
impl From<(i32, i32)> for Point {
    fn from(tuple: (i32, i32)) -> Self {
        Point { x: tuple.0, y: tuple.1 }
    }
}

// Display trait
impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}

fn main() {
    let article = Article {
        title: "Rust Traits".into(),
        content: "Traits are Rust's way of...".into(),
        author: "Alice".into(),
    };
    print_summary(&article);

    let p = Point::from((3, 4));
    println!("{}", p); // (3, 4)

    let items: Vec<Box<dyn Summary>> = vec![Box::new(article)];
    print_all(&items);
}
```

## Common Mistakes

```rust
// WRONG: Using dyn when impl Trait suffices (unnecessary heap allocation)
fn get_summary() -> Box<dyn Summary> {
    Box::new(Article { /* ... */ })
}

// CORRECT: impl Trait for single concrete type
fn get_summary() -> impl Summary {
    Article { /* ... */ }
}

// WRONG: Forgetting to implement required trait methods
trait Drawable {
    fn draw(&self);
    fn color(&self) -> &str;
}

impl Drawable for Circle {
    fn draw(&self) { /* ... */ }
    // Missing color() — compile error
}

// CORRECT: Implement all required methods or provide defaults in trait
trait Drawable {
    fn draw(&self);
    fn color(&self) -> &str {
        "black" // default
    }
}

// WRONG: Overusing generics — trait objects for many types
fn draw_all(shapes: &[impl Drawable]) { /* ... */ }

// CORRECT: Use trait objects when you need heterogeneous collections
fn draw_all(shapes: &[Box<dyn Drawable>]) {
    for shape in shapes {
        shape.draw();
    }
}

// WRONG: Implementing foreign trait on foreign type (orphan rule violation)
// impl std::fmt::Display for Vec<i32> { ... } // ERROR

// CORRECT: Use a newtype wrapper
struct DisplayVec(Vec<i32>);
impl std::fmt::Display for DisplayVec {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self.0)
    }
}
```

## Gotchas
- `impl Trait` in argument position = syntactic sugar for generics with trait bound
- `impl Trait` in return position = opaque type, one concrete type hidden from caller
- `dyn Trait` uses fat pointer (data + vtable) — 2x pointer size
- Orphan rule: you can implement a trait for a type only if either the trait or the type is defined in your crate
- `#[derive]` only works if all fields also implement the derived trait
- Associated types (`type Item`) are preferred when there's exactly one implementation per type
- Generic bounds on structs require the bound on the struct definition AND the impl block
- `Send` and `Sync` are auto-traits — derived automatically if all fields are Send/Sync

## Related
- rust/stdlib/ownership.md
- rust/stdlib/lifetimes.md
- rust/stdlib/result-option.md
