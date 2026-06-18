---
id: "rust-concurrency-tokio-select"
title: "tokio::select! Macro — Concurrent Operation Patterns"
language: "rust"
category: "concurrency"
subcategory: "async"
tags: ["rust", "tokio", "select", "async", "concurrency", "macro", "cancel-safety"]
version: "1.75+"
retrieval_hint: "Rust tokio select macro concurrent operation cancel safety timeout graceful shutdown"
last_verified: "2026-05-25"
confidence: "high"
---

# tokio::select! Macro — Concurrent Operation Patterns

## When to Use
- Waiting on multiple async operations and handling the first one that completes
- Implementing timeouts (wait for work OR deadline)
- Graceful shutdown (handle SIGTERM OR ongoing work)
- Racing multiple strategies and using the fastest result
- Multiplexing channels where you don't know which will fire next

## Standard Pattern

```rust
use tokio::select;
use tokio::time::{sleep, timeout, Duration};
use tokio::sync::mpsc;

// --- Basic select: work or timeout ---
async fn fetch_or_timeout(url: &str) -> Result<String, &'static str> {
    // This is equivalent to tokio::time::timeout()
    select! {
        result = fetch_data(url) => {
            result.map_err(|_| "fetch failed")
        }
        _ = sleep(Duration::from_secs(5)) => {
            Err("timeout after 5s")
        }
    }
}

// --- Graceful shutdown pattern ---
async fn run_server(mut shutdown_rx: mpsc::Receiver<()>) {
    loop {
        select! {
            // Biased: check shutdown first — ensures it takes priority
            biased;

            _ = shutdown_rx.recv() => {
                println!("Shutting down gracefully...");
                break;
            }
            // Regular work
            _ = process_next_request() => {
                // handle request
            }
        }
    }
}

// --- Race two strategies (use fastest result) ---
async fn fastest_route() -> &'static str {
    select! {
        result = route_a() => result,
        result = route_b() => result,
    }
}

async fn route_a() -> &'static str {
    sleep(Duration::from_millis(100)).await;
    "route_a (slow)"
}

async fn route_b() -> &'static str {
    sleep(Duration::from_millis(50)).await;
    "route_b (fast)"
}

// --- Channel multiplexing ---
async fn multiplex(
    mut rx1: mpsc::Receiver<String>,
    mut rx2: mpsc::Receiver<String>,
) {
    loop {
        select! {
            msg = rx1.recv() => {
                match msg {
                    Some(m) => println!("rx1: {}", m),
                    None => break, // channel closed
                }
            }
            msg = rx2.recv() => {
                match msg {
                    Some(m) => println!("rx2: {}", m),
                    None => break,
                }
            }
        }
    }
}

// --- Pattern: select loop with timeout and tick ---
async fn tick_loop() {
    let mut interval = tokio::time::interval(Duration::from_secs(1));

    loop {
        select! {
            _ = interval.tick() => {
                println!("tick every second");
            }
            _ = sleep(Duration::from_secs(5)) => {
                println!("5 seconds passed, exiting loop");
                break;
            }
        }
    }
}
```

## Common Mistakes

```rust
use tokio::sync::oneshot;

// WRONG: Non-cancel-safe operation in select! branch
// select! cancels the losing branches. Some operations cannot be safely cancelled.
async fn read_from_stream(stream: &mut TcpStream) -> Result<Vec<u8>, Error> {
    // This operation reads partial data. If cancelled mid-read,
    // the data is LOST and the stream state is corrupt.
    select! {
        data = stream.read_to_end() => data,
        _ = sleep(Duration::from_secs(1)) => Err(Error::Timeout),
    }
}

// CORRECT: Only use cancel-safe operations in select!
// Cancel-safe tokio operations include:
//   - tokio::sync::oneshot::Receiver::recv()
//   - tokio::sync::mpsc::Receiver::recv()
//   - tokio::time::sleep/tick
//   - tokio::sync::Semaphore::acquire()
//
// NOT cancel-safe:
//   - tokio::io::AsyncRead/AsyncWrite (partial read/write)
//   - tokio::net::TcpStream::read_to_end()
//   - tokio::process::Child::wait()
//   - std::future::Future (any generic future)

// WRONG: Borrowing without &mut in select! branch
async fn bad_borrow(value: &mut String) {
    select! {
        _ = async { value.push_str("modified") } => {
            // ERROR: cannot borrow `value` as mutable more than once
        }
        _ = sleep(Duration::from_millis(1)) => {
            // This also needs mutable access? No, but select! needs
            // to know the borrow doesn't conflict.
        }
    }
}

// CORRECT: Use &mut for mutable access in select! branches
async fn good_borrow(value: &mut String) {
    select! {
        result = modify_value(value) => {
            println!("modified: {}", result);
        }
        _ = sleep(Duration::from_millis(1)) => {
            println!("timed out");
        }
    }
}

async fn modify_value(value: &mut String) -> &str {
    value.push_str("_modified");
    "done"
}

// WRONG: Assuming select! is unbiased (random)
// Tokio's select! is BIASED — the first branch that's ready always wins.
// This can cause starvation for later branches.
loop {
    select! {
        msg = fast_channel.recv() => {
            // This always wins: fast_channel is checked first
            handle(msg);
        }
        msg = slow_channel.recv() => {
            // This almost never fires even if both are ready
            handle(msg);
        }
    }
}

// CORRECT: Use tokio::select! with `biased` keyword to make it explicit,
// or restructure so higher-priority branches don't starve others.
// If fairness matters, rotate the order periodically:
loop {
    select! {
        msg = slow_channel.recv() => handle(msg),
        msg = fast_channel.recv() => handle(msg),
    }
    // Rotate for fairness
    std::mem::swap(&mut fast_channel, &mut slow_channel);
}
```

## Gotchas
- **`select!` is biased by default (since Tokio 1.x):** Earlier branches have priority. If both branches can proceed simultaneously, the first branch wins. Use `select! { biased; ... }` to make this explicit, or use `select! { ... }` which ALSO prefers earlier branches. Tokio's default is biased, NOT random.
- **Cancel safety is YOUR responsibility:** `select!` drops the losing future. If that future was in the middle of a non-atomic operation (e.g., partial read from a socket), that operation is corrupted. Only `select!` on cancel-safe futures unless you know what you're doing. Most tokio primitives (channels, timers, semaphores) are cancel-safe; I/O operations are NOT.
- **`&mut` is required for stateful branches:** If a future mutates state, you need `&mut` in the `select!` branch. Without it, the future can't borrow the state. If you get confusing borrow-checker errors from `select!`, check if you're missing `&mut` on the async operation.
- **`&mut` on a branch future prevents reuse after select!:** After `select!`, the losing future was dropped. If you borrowed `&mut something` in a branch, that borrow might still be active (logically). Move the future creation into the `select!` branch or recreate it in a loop.
- **`select!` with `tokio::pin!`:** For non-trivial futures in a loop, use `tokio::pin!` to avoid re-allocating the future on every iteration:

```rust
use tokio::pin;

async fn select_loop() {
    let slow_future = slow_operation();
    pin!(slow_future);  // Pin the future so it's reused

    loop {
        select! {
            result = &mut slow_future => break result,
            _ = sleep(Duration::from_secs(1)) => println!("waiting..."),
        }
    }
}
```

## Related
- rust/concurrency/async-tokio.md
- rust/concurrency/async-traits.md
