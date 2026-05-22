---
id: "rust-concurrency-async-tokio"
title: "Async with Tokio"
language: "rust"
category: "concurrency"
tags: ["async", "await", "tokio", "spawn", "channel", "mutex", "select"]
version: "1.75+"
retrieval_hint: "async await tokio spawn select channel Mutex concurrency task"
last_verified: "2026-05-22"
confidence: "high"
---

# Async with Tokio

## When to Use
- I/O-bound concurrency (HTTP clients, database queries, file I/O)
- Handling thousands of simultaneous connections
- Building async web servers (axum, actix-web)
- Coordinating multiple concurrent operations

## Standard Pattern

```rust
use tokio::sync::{mpsc, oneshot, Mutex};
use tokio::time::{sleep, Duration};
use std::sync::Arc;

// Entry point
#[tokio::main]
async fn main() {
    // Spawn concurrent tasks
    let handle = tokio::spawn(async {
        sleep(Duration::from_millis(100)).await;
        "task result"
    });
    let result = handle.await.unwrap();
    println!("Got: {}", result);

    // Channel for message passing
    let (tx, mut rx) = mpsc::channel::<String>(32);

    let tx1 = tx.clone();
    tokio::spawn(async move {
        tx1.send("hello from task 1".into()).await.unwrap();
    });

    let tx2 = tx.clone();
    tokio::spawn(async move {
        tx2.send("hello from task 2".into()).await.unwrap();
    });
    drop(tx); // Close channel when all senders drop

    while let Some(msg) = rx.recv().await {
        println!("Received: {}", msg);
    }

    // Join multiple futures
    let (a, b, c) = tokio::join!(
        fetch_data("url1"),
        fetch_data("url2"),
        fetch_data("url3"),
    );
    println!("{}, {}, {}", a, b, c);

    // select! — first to complete wins
    tokio::select! {
        val = fetch_data("fast") => println!("Fast won: {}", val),
        _ = sleep(Duration::from_secs(5)) => println!("Timed out"),
    }

    // Shared state with Arc<Mutex<T>>
    let counter = Arc::new(Mutex::new(0u64));
    let mut handles = vec![];
    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        handles.push(tokio::spawn(async move {
            let mut num = counter.lock().await;
            *num += 1;
        }));
    }
    for h in handles {
        h.await.unwrap();
    }
    println!("Counter: {}", *counter.lock().await);

    // Oneshot channel for single response
    let (tx, rx) = oneshot::channel();
    tokio::spawn(async move {
        tx.send(42).unwrap();
    });
    let val = rx.await.unwrap();
    println!("Got: {}", val);
}

async fn fetch_data(url: &str) -> String {
    sleep(Duration::from_millis(50)).await;
    format!("data from {}", url)
}
```

## Common Mistakes

```rust
// WRONG: Using std::sync::Mutex in async code
use std::sync::Mutex;
async fn bad() {
    let m = Mutex::new(0);
    let guard = m.lock().unwrap(); // Blocks the executor thread!
    // Other tasks on this thread cannot run
}

// CORRECT: Use tokio::sync::Mutex for async
use tokio::sync::Mutex;
async fn good() {
    let m = Mutex::new(0);
    let mut guard = m.lock().await; // Yields to executor
    *guard += 1;
}

// WRONG: Holding Mutex guard across .await points (potential deadlock)
async fn bad_pattern(m: &Mutex<Vec<String>>) {
    let mut guard = m.lock().await;
    guard.push(fetch_remote().await); // Holds lock during I/O!
}

// CORRECT: Minimize critical section
async fn good_pattern(m: &Mutex<Vec<String>>) {
    let data = fetch_remote().await;
    let mut guard = m.lock().await;
    guard.push(data); // Lock held briefly
}

// WRONG: Spawning tasks without handling JoinHandle
tokio::spawn(async { /* fire and forget, errors lost */ });

// CORRECT: At minimum, log on task panic
let handle = tokio::spawn(async { work().await });
if let Err(e) = handle.await {
    eprintln!("Task panicked: {}", e);
}

// WRONG: Using block_on inside async context
async fn nested() {
    tokio::runtime::Handle::current().block_on(async { /* ... */ });
}

// CORRECT: Just await directly
async fn nested() {
    some_future().await;
}
```

## Gotchas
- `tokio::spawn` requires the future to be `'static + Send` — use `move` closures
- `select!` cancels the other branches when one completes — be careful with cleanup
- `#[tokio::main]` creates a multi-threaded runtime by default; use `#[tokio::main(flavor = "current_thread")]` for single-threaded
- `tokio::spawn` returns `JoinHandle` — `.await` it to propagate panics
- Prefer `tokio::sync::RwLock` over `Mutex` when reads dominate writes
- `spawn_blocking` moves CPU-heavy work off the async runtime
- Channels: `mpsc` for multiple producers, `oneshot` for single response, `broadcast` for fan-out, `watch` for latest value
- Async destructors (Drop) cannot `.await` — use explicit cleanup methods

## Related
- rust/stdlib/ownership.md
- rust/stdlib/result-option.md
- rust/web/axum-basics.md
