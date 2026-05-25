---
id: "rust-websocket-patterns"
title: "WebSocket Patterns: tokio-tungstenite, Axum WS, Real-Time"
language: "rust"
category: "web"
tags: ["rust", "websocket", "tokio-tungstenite", "axum", "real-time", "streaming"]
version: "n/a"
retrieval_hint: "rust websocket tokio-tungstenite axum ws real-time streaming bidirectional"
last_verified: "2026-05-24"
confidence: "high"
---

# WebSocket Patterns: tokio-tungstenite, Axum WS, Real-Time

## When to Use
- Real-time bidirectional communication (chat, notifications)
- Live data streaming (price feeds, logs, metrics)
- Replacing polling with push-based updates
- Axum applications needing WebSocket support

## Standard Pattern

```rust
use axum::{
    extract::ws::{WebSocket, WebSocketUpgrade, Message},
    response::IntoResponse,
    routing::get,
    Router,
};
use futures::{SinkExt, StreamExt};
use std::sync::Arc;
use tokio::sync::broadcast;

// === Dependencies (Cargo.toml) ===
// axum = { version = "0.7", features = ["ws"] }
// tokio = { version = "1", features = ["full"] }
// futures = "0.3"
// tokio-tungstenite = "0.21"  // For non-axum WS client usage
// serde = { version = "1", features = ["derive"] }
// serde_json = "1"


// === Shared State (Broadcast Channel) ===

#[derive(Clone)]
struct AppState {
    tx: broadcast::Sender<String>,
}

fn app_state() -> AppState {
    let (tx, _) = broadcast::channel(100);
    AppState { tx }
}


// === Axum WebSocket Upgrade ===

async fn ws_handler(
    ws: WebSocketUpgrade,
    axum::extract::State(state): axum::extract::State<AppState>,
) -> impl IntoResponse {
    ws.on_upgrade(move |socket| handle_socket(socket, state))
}


// === WebSocket Handler ===

async fn handle_socket(socket: WebSocket, state: AppState) {
    let (mut sender, mut receiver) = socket.split();

    // Subscribe to broadcast channel
    let mut rx = state.tx.subscribe();

    // Spawn task to forward broadcast messages to client
    let mut send_task = tokio::spawn(async move {
        while let Ok(msg) = rx.recv().await {
            if sender.send(Message::Text(msg.into())).await.is_err() {
                break;  // Client disconnected
            }
        }
    });

    // Clone sender for echo/response
    let mut send_clone = state.tx.clone();

    // Handle incoming messages from client
    let recv_task = tokio::spawn(async move {
        while let Some(Ok(msg)) = receiver.next().await {
            match msg {
                Message::Text(text) => {
                    // Echo or broadcast the message
                    let _ = send_clone.send(text);
                }
                Message::Binary(data) => {
                    // Handle binary data
                    if let Ok(text) = String::from_utf8(data) {
                        let _ = send_clone.send(text);
                    }
                }
                Message::Ping(_) | Message::Pong(_) => {
                    // Handled automatically by axum
                }
                Message::Close(_) => break,
            }
        }
    });

    // Wait for either task to finish (client disconnect)
    tokio::select! {
        _ = send_task => {},
        _ = recv_task => {},
    }
}


// === Client Pattern (tokio-tungstenite) ===

async fn ws_client() -> Result<(), Box<dyn std::error::Error>> {
    use tokio_tungstenite::connect_async;
    use futures_util::StreamExt;

    let url = url::Url::parse("wss://example.com/ws")?;
    let (ws_stream, _) = connect_async(url).await?;

    let (mut write, mut read) = ws_stream.split();

    // Send a message
    write.send(Message::Text("hello".to_string().into())).await?;

    // Read responses
    while let Some(msg) = read.next().await {
        let msg = msg?;
        if let Some(text) = msg.to_text().ok() {
            println!("Received: {text}");
        }
    }

    Ok(())
}


// === Broadcast Pattern (Typed) ===

use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
enum ServerEvent {
    Message { user: String, text: String },
    Notification { kind: String, payload: String },
    UserJoined { user_id: i64 },
}

async fn broadcast_event(tx: &broadcast::Sender<String>, event: &ServerEvent) {
    if let Ok(json) = serde_json::to_string(event) {
        let _ = tx.send(json);
    }
}


// === Router Setup ===

fn build_ws_router() -> Router {
    let state = app_state();

    Router::new()
        .route("/ws", get(ws_handler))
        .with_state(state)
}
```

## Common Mistakes

```rust
// WRONG: Blocking inside WebSocket handler (blocks the task)
async fn handle_socket(socket: WebSocket) {
    // std::thread::sleep(Duration::from_secs(1));  // Blocks!
    // Use tokio::time::sleep instead
}

// CORRECT: Use async sleep
tokio::time::sleep(Duration::from_secs(1)).await;


// WRONG: Not handling ping/pong (connection timeout)
// Axum handles ping/pong automatically, but if using tungstenite directly:
// Server sends ping, expects pong within timeout

// CORRECT: Set ping interval on the websocket stream
// WebSocketConfig::default().ping_interval = Some(Duration::from_secs(10));


// WRONG: Unbounded channel buffer (memory leak)
let (tx, _) = broadcast::channel(10_000_000);  // Too large!

// CORRECT: Use reasonable buffer with backpressure
let (tx, _) = broadcast::channel(100);
// If client can't keep up, messages are dropped (lagged)


// WRONG: Sending to a disconnected client (error ignored)
let _ = sender.send(Message::Text(msg.into())).await;
// If client disconnected, this fails silently — possible zombie task

// CORRECT: Break out of the loop on error
if sender.send(Message::Text(msg.into())).await.is_err() {
    break;  // Client disconnected, stop sending
}


// WRONG: Mixing WS upgrades and regular routes without path distinction
// WS upgrade handler should be on a dedicated path

// CORRECT: Keep WS on separate path from REST API
// "/ws" → WebSocket upgrade
// "/api/" → REST handlers
```

## Gotchas
- **WebSocket vs SSE**: WebSockets are bidirectional. If you only need server-to-client streaming, Server-Sent Events (SSE) via `axum::response::sse` are simpler, work through HTTP, and have better browser support.
- **Connection limit**: Each WebSocket consumes a file descriptor and a tokio task. For 10K concurrent connections, ensure your system limits (`ulimit -n`) and tokio runtime are configured accordingly.
- **Graceful shutdown**: WebSocket connections keep the server alive. Use `axum::serve` with a shutdown signal and `socket.on_closed()` to drain connections during shutdown.
- **WSS vs WS in production**: Always use WSS (WSS over TLS) in production. Browsers block mixed content — if your page is served over HTTPS, WebSocket connections must also be encrypted.
- **Message size limits**: Axum has a 64KB default message size for WebSocket messages. Configure `WebSocketConfig::default().max_message_size` for larger payloads.
- **Reconnection logic**: Clients should implement exponential backoff reconnection. WebSocket connections drop frequently (network changes, proxies, server restarts). Don't treat disconnection as permanent failure.
- **broadcast::Sender::send vs try_send**: `send` is async and waits for capacity. For WebSocket broadcasts, prefer `try_send` or check `receiver_count()` to avoid blocking the sender on slow consumers.

## Related
- rust/web/axum-middleware.md
- rust/stdlib/http-client.md
- rust/testing/integration.md
