---
id: "python-stdlib-socket-programming"
title: "Socket Programming Basics"
language: "python"
category: "stdlib"
subcategory: "networking"
tags: ["socket", "tcp", "udp", "network", "server", "client", "connection"]
version: "3.10+"
retrieval_hint: "socket TCP UDP server client network connection bind listen accept"
last_verified: "2026-05-22"
confidence: "high"
---

# Socket Programming Basics

## When to Use
- Building custom network protocols or low-level servers
- Understanding how HTTP, WebSocket, and other protocols work under the hood
- Inter-process communication (IPC) via Unix domain sockets
- Network debugging, port scanning, or connectivity testing

## Standard Pattern

```python
import socket
import threading
from typing import Optional


# --- TCP Server ---
def run_tcp_server(host: str = "127.0.0.1", port: int = 8080) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(5)
        print(f"Listening on {host}:{port}")

        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()


def handle_client(conn: socket.socket, addr: tuple) -> None:
    with conn:
        print(f"Connected: {addr}")
        while True:
            data = conn.recv(4096)
            if not data:
                break
            conn.sendall(b"Echo: " + data)  # Echo back


# --- TCP Client ---
def tcp_client(host: str = "127.0.0.1", port: int = 8080, message: str = "Hello") -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5.0)
        sock.connect((host, port))
        sock.sendall(message.encode())
        response = sock.recv(4096)
        return response.decode()


# --- UDP Server ---
def run_udp_server(host: str = "127.0.0.1", port: int = 8081) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind((host, port))
        print(f"UDP listening on {host}:{port}")
        while True:
            data, addr = server.recvfrom(4096)
            server.sendto(b"Ack: " + data, addr)


# --- UDP Client ---
def udp_client(host: str = "127.0.0.1", port: int = 8081, message: str = "Hello") -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(5.0)
        sock.sendto(message.encode(), (host, port))
        response, _ = sock.recvfrom(4096)
        return response.decode()


# --- Unix Domain Socket (IPC) ---
def run_unix_server(socket_path: str = "/tmp/myapp.sock") -> None:
    import os
    if os.path.exists(socket_path):
        os.unlink(socket_path)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(socket_path)
        server.listen(5)
        conn, _ = server.accept()
        with conn:
            data = conn.recv(4096)
            conn.sendall(b"Got: " + data)
```

## Common Mistakes

```python
# WRONG: Not setting SO_REUSEADDR (address already in use on restart)
server.bind((host, port))  # Fails if server just restarted

# CORRECT: Allow address reuse
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((host, port))

# WRONG: Blocking recv without timeout
data = sock.recv(4096)  # Blocks forever if client never sends

# CORRECT: Set timeout
sock.settimeout(5.0)
try:
    data = sock.recv(4096)
except socket.timeout:
    print("Timed out")

# WRONG: Not handling partial sends
sock.sendall(large_data)  # sendall handles this, but send() doesn't!

# CORRECT: Use sendall() for reliable delivery
sock.sendall(large_data)  # Retries until all bytes are sent

# WRONG: Binding to 0.0.0.0 in development
server.bind(("0.0.0.0", 8080))  # Exposes to all network interfaces

# CORRECT: Bind to localhost in development
server.bind(("127.0.0.1", 8080))  # Only local access
```

## Gotchas
- `socket.recv(4096)` returns up to 4096 bytes — it may return fewer (always check length)
- TCP is a stream protocol — there are no message boundaries; implement your own framing
- `SO_REUSEADDR` prevents "Address already in use" errors on server restart
- `socket.send()` may send fewer bytes than requested — use `sendall()` for guaranteed delivery
- Use `threading` or `selectors` module for handling multiple clients (or just use `asyncio`)
- UDP is connectionless and unreliable — messages may arrive out of order or not at all
- Unix domain sockets (`AF_UNIX`) are faster than TCP for local IPC (no network overhead)
- For production servers, use `asyncio` or a framework like `uvicorn`, not raw sockets

## Related
- python/concurrency/asyncio-basics.md
- python/stdlib/httpx.md
- python/web/fastapi/basics.md
