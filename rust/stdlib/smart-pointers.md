---
id: "rust-stdlib-smart-pointers"
title: "Rust Smart Pointers: Box, Rc, Arc, and Interior Mutability"
language: "rust"
category: "stdlib"
subcategory: "memory"
tags: ["rust", "box", "rc", "arc", "refcell", "mutex", "smart-pointer", "interior-mutability"]
version: "1.75+"
retrieval_hint: "Rust Box Rc Arc RefCell Mutex RwLock smart pointer interior mutability weak reference"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust Smart Pointers: Box, Rc, Arc, and Interior Mutability

## When to Use

- `Box<T>`: Single owner heap allocation, fixed-size type erasure, recursive types
- `Rc<T>`: Multiple ownership within a single thread (reference counting)
- `Arc<T>`: Multiple ownership across threads (atomic reference counting)
- `RefCell<T>`: Interior mutability with borrow checking at runtime (single thread)
- `Mutex<T>` / `RwLock<T>`: Interior mutability across threads (synchronized)
- `Weak<T>`: Breaking reference cycles in `Rc` or `Arc` graphs

Quick decision tree:
```text
Need heap allocation with single owner? -> Box<T>
Need shared ownership on single thread? -> Rc<T>
Need shared ownership across threads?   -> Arc<T>
Need to mutate through shared ref?      -> RefCell<T> (single) or Mutex<T>/<RwLock<T> (multi)
Need to break reference cycles?         -> Weak<T>
```

## Standard Pattern

```rust
use std::cell::RefCell;
use std::rc::{Rc, Weak};
use std::sync::{Arc, Mutex, RwLock};

// --- Box<T>: heap allocation with single owner ---
fn build_tree() -> Box<TreeNode> {
    Box::new(TreeNode {
        value: 42,
        left: Some(Box::new(TreeNode { value: 10, left: None, right: None })),
        right: None,
    })
}

struct TreeNode {
    value: i32,
    left: Option<Box<TreeNode>>,
    right: Option<Box<TreeNode>>,
}

// --- Rc<T>: shared ownership, single thread ---
fn shared_data() -> (Rc<Vec<i32>>, Rc<Vec<i32>>) {
    let data = Rc::new(vec![1, 2, 3, 4, 5]);
    let ref1 = Rc::clone(&data);  // increments refcount, cheap
    let ref2 = Rc::clone(&data);
    println!("refcount: {}", Rc::strong_count(&data)); // 3
    (ref1, ref2)
}

// --- RefCell<T>: interior mutability ---
fn interior_mutability() {
    let shared_list: Rc<RefCell<Vec<String>>> = Rc::new(RefCell::new(Vec::new()));
    let list_ref = Rc::clone(&shared_list);

    // Mutate through a shared Rc — borrow enforced at runtime
    shared_list.borrow_mut().push("hello".to_string());
    list_ref.borrow_mut().push("world".to_string());

    println!("{:?}", shared_list.borrow()); // ["hello", "world"]
}

// --- Arc<Mutex<T>>: shared mutable state across threads ---
use std::thread;

fn shared_counter() -> Arc<Mutex<i32>> {
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];

    for _ in 0..4 {
        let c = Arc::clone(&counter);
        handles.push(thread::spawn(move || {
            let mut guard = c.lock().unwrap();
            *guard += 1;
            // guard dropped here, releasing the lock
        }));
    }

    for h in handles {
        h.join().unwrap();
    }

    let final_val = *counter.lock().unwrap();
    assert_eq!(final_val, 4);
    counter
}

// --- Arc<RwLock<T>>: many readers OR one writer ---
fn shared_config() -> Arc<RwLock<Config>> {
    let config = Arc::new(RwLock::new(Config { debug: false }));

    // Multiple readers simultaneously
    let r1 = Arc::clone(&config);
    let reader1 = thread::spawn(move || {
        let cfg = r1.read().unwrap();
        println!("debug: {}", cfg.debug);
    });

    let r2 = Arc::clone(&config);
    let reader2 = thread::spawn(move || {
        let cfg = r2.read().unwrap();
        println!("debug: {}", cfg.debug);
    });

    // Single writer (blocks until all readers done)
    let w = Arc::clone(&config);
    let writer = thread::spawn(move || {
        let mut cfg = w.write().unwrap();
        cfg.debug = true;
    });

    reader1.join().unwrap();
    reader2.join().unwrap();
    writer.join().unwrap();

    config
}

#[derive(Debug)]
struct Config {
    debug: bool,
}

// --- Weak<T>: breaking reference cycles ---
struct Node {
    value: i32,
    parent: RefCell<Weak<Node>>,
    children: RefCell<Vec<Rc<Node>>>,
}

fn build_graph() {
    let root = Rc::new(Node {
        value: 0,
        parent: RefCell::new(Weak::new()),
        children: RefCell::new(vec![]),
    });

    let child = Rc::new(Node {
        value: 1,
        parent: RefCell::new(Rc::downgrade(&root)), // Weak reference
        children: RefCell::new(vec![]),
    });

    root.children.borrow_mut().push(child);

    // Access parent through Weak::upgrade() -> Option<Rc<Node>>
    let root_node = root.children.borrow()[0]
        .parent
        .borrow()
        .upgrade()
        .expect("parent should exist");
    println!("parent value: {}", root_node.value); // 0
}
```

## Common Mistakes

```rust
// WRONG: Using Mutex without locking before access
let data = Arc::new(Mutex::new(vec![1, 2, 3]));
let val = data[0]; // Compiler error: cannot index Mutex directly

// CORRECT: Lock the mutex to get a guard, then access
let data = Arc::new(Mutex::new(vec![1, 2, 3]));
let val = data.lock().unwrap()[0];


// WRONG: Calling borrow_mut while a borrow is still alive (panics at runtime)
let cell = RefCell::new(vec![1, 2, 3]);
let _borrow = cell.borrow();        // shared borrow
let _mut_borrow = cell.borrow_mut(); // PANIC: already borrowed

// CORRECT: Drop the shared borrow before mutably borrowing
let cell = RefCell::new(vec![1, 2, 3]);
{
    let _borrow = cell.borrow();
    println!("{:?}", _borrow);
} // _borrow dropped here
let mut _mut_borrow = cell.borrow_mut();
_mut_borrow.push(4);


// WRONG: Using Rc instead of Arc across threads (won't compile)
let data = Rc::new(42);
thread::spawn(move || {
    println!("{}", data); // ERROR: Rc is not Send
});

// CORRECT: Use Arc for cross-thread sharing
let data = Arc::new(42);
thread::spawn(move || {
    println!("{}", data);
});


// WRONG: Forgetting to handle Weak::upgrade() returning Option
let weak: Weak<Vec<i32>> = Weak::new();
let rc = weak.unwrap(); // WRONG: this is Mutex's unwrap, not Weak's upgrade

// CORRECT: Always handle the Option from Weak::upgrade()
let weak: Weak<Vec<i32>> = Weak::new();
match weak.upgrade() {
    Some(rc) => println!("{:?}", rc),
    None => println!("value has been dropped"),
}


// WRONG: Queueing MutexGuard across .await points (holding guard over await)
async fn bad_pattern(data: Arc<Mutex<Vec<i32>>>) {
    let mut guard = data.lock().unwrap();
    guard.push(1);
    some_async_fn().await; // BAD: holding lock across await
}

// CORRECT: Drop the guard before .await or use a scope
async fn good_pattern(data: Arc<Mutex<Vec<i32>>>) {
    {
        let mut guard = data.lock().unwrap();
        guard.push(1);
    } // guard dropped here
    some_async_fn().await;
}
```

## Gotchas
- `RefCell<T>` borrow rules are enforced at **runtime**, not compile time — two active `borrow_mut()` calls will cause a thread panic
- `Rc<T>` is not `Send` or `Sync` — the compiler will refuse to share it across threads; use `Arc<T>` instead
- `Mutex::lock()` returns `Result<MutexGuard, PoisonError>` — if another thread panics while holding the lock, the mutex is "poisoned"
- `Arc::clone(&x)` only clones the pointer (increments count); it does NOT deep-clone the inner data
- `Weak::upgrade()` returns `Option<Rc<T>>` — the inner value may have already been dropped; never unwrap without checking
- `Box<T>` has zero overhead over a raw pointer — it's a guaranteed-unique heap pointer with no refcounting
- Holding a `MutexGuard` across an `.await` point in async code can cause deadlocks and scheduler issues

## Related
- rust/stdlib/ownership.md
- rust/stdlib/lifetimes.md
- rust/stdlib/collections.md
