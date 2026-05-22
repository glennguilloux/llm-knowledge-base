---
id: "typescript-runtime-node-http"
title: "Node.js HTTP Server and Client"
language: "typescript"
category: "stdlib"
subcategory: "http"
tags: ["http", "server", "client", "request", "response", "node"]
version: "18+"
retrieval_hint: "Node.js HTTP server client request response"
last_verified: "2026-05-22"
confidence: "high"
---

# Node.js HTTP Server and Client

## When to Use
- Building HTTP servers without frameworks
- Making HTTP requests with native APIs
- Understanding HTTP fundamentals
- Low-level server customization

## Standard Pattern

```typescript
import { createServer, IncomingMessage, ServerResponse } from 'http';
import { request as httpRequest } from 'https';

// Simple HTTP server
const server = createServer((req: IncomingMessage, res: ServerResponse) => {
  const url = new URL(req.url || '/', `http://${req.headers.host}`);
  
  if (url.pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok' }));
    return;
  }
  
  if (url.pathname === '/api/users' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify([{ id: 1, name: 'Alice' }]));
    return;
  }
  
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Not found' }));
});

server.listen(3000, () => {
  console.log('Server running on http://localhost:3000');
});

// HTTP client (native)
async function fetchUrl(url: string): Promise<string> {
  return new Promise((resolve, reject) => {
    httpRequest(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
      res.on('error', reject);
    }).on('error', reject).end();
  });
}

// Better: Use fetch() (Node 18+)
async function fetchJSON<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}
```

## Common Mistakes

```typescript
// WRONG: Not handling errors
const server = createServer((req, res) => {
  throw new Error('Oops');  // Crashes server!
});

// CORRECT: Wrap in try/catch
const server = createServer((req, res) => {
  try {
    handleRequest(req, res);
  } catch (error) {
    res.writeHead(500);
    res.end('Internal Server Error');
  }
});

// WRONG: Using http.request for HTTPS
import { request } from 'http';
request('https://api.example.com');  // Wrong module!

// CORRECT: Use https for HTTPS URLs
import { request } from 'https';
request('https://api.example.com');
```

## Gotchas
- `createServer` callback receives `IncomingMessage` and `ServerResponse`
- `req.url` may be undefined — default to '/'
- `res.writeHead()` must be called before `res.end()`
- Use `fetch()` (Node 18+) instead of `http.request` for clients
- `http` for HTTP, `https` for HTTPS
- Server doesn't automatically parse JSON body — use `req.on('data')`
- Use `req.headers.host` for the hostname

## Related
- typescript/runtime/node/fs.md
- typescript/runtime/node/streams.md
