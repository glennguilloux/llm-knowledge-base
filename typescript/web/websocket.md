---
id: "typescript-web-websocket"
title: "WebSocket with ws and socket.io"
language: "typescript"
category: "web"
tags: ["typescript", "websocket", "ws", "socket-io", "real-time"]
version: "5.0+"
retrieval_hint: "TypeScript WebSocket ws socket.io real-time chat"
last_verified: "2026-05-24"
confidence: "high"
---

# WebSocket with ws and socket.io

## When to Use
- Real-time communication (chat, notifications)
- Live data updates (dashboards, stock prices)
- Collaborative editing
- Bidirectional server-client communication

## Standard Pattern

```typescript
// Server with ws library
import { WebSocketServer, WebSocket } from "ws";

const wss = new WebSocketServer({ port: 8080 });

const clients = new Set<WebSocket>();

wss.on("connection", (ws: WebSocket) => {
  clients.add(ws);
  console.log("Client connected");

  ws.on("message", (data: Buffer) => {
    const message = JSON.parse(data.toString());
    // Broadcast to all clients
    for (const client of clients) {
      if (client !== ws && client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify(message));
      }
    }
  });

  ws.on("close", () => {
    clients.delete(ws);
    console.log("Client disconnected");
  });

  ws.on("error", (error: Error) => {
    console.error("WebSocket error:", error);
    clients.delete(ws);
  });
});

// Client with native WebSocket
class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnects = 5;

  connect(url: string): void {
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log("Connected");
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnects) {
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect(url);
        }, 1000 * Math.pow(2, this.reconnectAttempts));
      }
    };
  }

  send(data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  private handleMessage(data: unknown): void {
    console.log("Received:", data);
  }
}

// socket.io (higher-level, with rooms and auto-reconnect)
import { Server } from "socket.io";

const io = new Server(3000, {
  cors: { origin: "http://localhost:5173" },
});

io.on("connection", (socket) => {
  console.log("User connected:", socket.id);

  socket.join("general");

  socket.on("message", (data: { room: string; text: string }) => {
    io.to(data.room).emit("message", {
      user: socket.id,
      text: data.text,
      timestamp: Date.now(),
    });
  });

  socket.on("join-room", (room: string) => {
    socket.join(room);
    io.to(room).emit("user-joined", socket.id);
  });

  socket.on("disconnect", () => {
    console.log("User disconnected:", socket.id);
  });
});
```

## Common Mistakes

```typescript
// WRONG: No reconnection logic
const ws = new WebSocket("ws://localhost:8080");
ws.onclose = () => console.log("Disconnected");  // Gone forever

// CORRECT: Implement reconnection with backoff
ws.onclose = () => {
  const delay = Math.min(1000 * Math.pow(2, attempts), 30000);
  setTimeout(() => connect(), delay);
};

// WRONG: Not handling binary data
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);  // Fails on binary frames
};

// CORRECT: Check data type
ws.onmessage = (event) => {
  if (typeof event.data === "string") {
    const data = JSON.parse(event.data);
  } else {
    // Handle binary (ArrayBuffer)
  }
};

// WRONG: Sending without checking ready state
ws.send(JSON.stringify(data));  // May throw if not OPEN

// CORRECT: Check state
if (ws.readyState === WebSocket.OPEN) {
  ws.send(JSON.stringify(data));
}

// WRONG: No heartbeat — stale connections accumulate
// CORRECT: Implement ping/pong
setInterval(() => {
  ws.ping();
}, 30000);

ws.on("pong", () => {
  lastPong = Date.now();
});
```

## Gotchas
- Native `WebSocket` is available in browsers and Node.js 21+ — `ws` is more mature for servers
- `socket.io` adds rooms, namespaces, and auto-reconnect — but adds protocol overhead
- WebSocket connections are stateful — horizontal scaling requires sticky sessions or Redis adapter
- `ws` library doesn't handle reconnection — implement exponential backoff yourself
- CORS for WebSocket uses the `Origin` header — configure in socket.io or ws server
- Binary data can be sent as ArrayBuffer or Buffer — more efficient than JSON for large payloads
- WebSocket upgrade happens over HTTP — proxy servers must support `Upgrade` headers
- `wss://` is WebSocket over TLS — use in production, `ws://` for local dev only
- Heartbeat (ping/pong) detects dead connections — essential for production

## Related
- python/web/websocket.md
- typescript/web/express-server.md
- typescript/stdlib/async-patterns.md
