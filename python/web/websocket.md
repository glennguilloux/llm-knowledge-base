---
id: "python-web-websocket"
title: "WebSocket Patterns"
language: "python"
category: "web"
tags: ["websocket", "ws", "real-time", "async", "fastapi"]
version: "3.10+"
retrieval_hint: "WebSocket real-time chat live update connection"
last_verified: "2026-05-22"
confidence: "high"
---

# WebSocket Patterns

## When to Use
- Real-time communication (chat, notifications)
- Live data updates (stock prices, dashboards)
- Collaborative editing
- Server-sent events alternative (bidirectional)

## Standard Pattern

```python
# FastAPI WebSocket
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import json

app = FastAPI()

# Simple echo WebSocket
@app.websocket("/ws/echo")
async def websocket_echo(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        pass

# Connection manager for broadcasting
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        self.active_connections.setdefault(room, []).append(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        self.active_connections.get(room, []).remove(websocket)

    async def broadcast(self, message: str, room: str, exclude: WebSocket = None):
        for conn in self.active_connections.get(room, []):
            if conn != exclude and conn.client_state == WebSocketState.CONNECTED:
                await conn.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/chat/{room}")
async def chat_room(websocket: WebSocket, room: str):
    await manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(
                json.dumps({"user": data["user"], "message": data["message"]}),
                room=room,
                exclude=websocket,
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
        await manager.broadcast(
            json.dumps({"system": "User left"}),
            room=room,
        )

# Client-side usage
import websockets
import asyncio

async def chat_client():
    async with websockets.connect("ws://localhost:8000/ws/echo") as ws:
        await ws.send("Hello!")
        response = await ws.recv()
        print(response)
```

## Common Mistakes

```python
# WRONG: Not handling disconnection
@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()  # Crashes on disconnect

# CORRECT: Handle WebSocketDisconnect
@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        pass  # Client disconnected gracefully

# WRONG: Sending to closed connection
await closed_websocket.send_text("data")  # RuntimeError

# CORRECT: Check connection state
if websocket.client_state == WebSocketState.CONNECTED:
    await websocket.send_text("data")

# WRONG: No heartbeat/ping — stale connections accumulate
# CORRECT: Add ping interval
@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    websocket.ping_interval = 30  # seconds
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        pass
```

## Gotchas
- WebSocket connections are long-lived — handle cleanup on disconnect
- `WebSocketDisconnect` is raised when the client closes the connection
- Broadcasting to many clients requires a connection manager pattern
- WebSocket in FastAPI is async — use `await` for all operations
- `websockets` library is for clients; FastAPI uses `starlette.websockets`
- Binary data can be sent with `send_bytes` / `receive_bytes`
- WebSocket headers are set during the handshake — can't change after connect
- Production deployments need sticky sessions or a message broker (Redis Pub/Sub) for horizontal scaling

## Related
- python/web/fastapi/basics.md
- python/stdlib/asyncio-basics.md
- typescript/web/websocket.md
