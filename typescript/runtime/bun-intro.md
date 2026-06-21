---
id: "typescript-runtime-bun-intro"
title: "Bun Runtime — Key Patterns and Differences from Node.js"
language: "typescript"
category: "stdlib"
subcategory: "bun"
tags: ["bun", "runtime", "nodejs", "typescript", "bundler", "test-runner", "javascript"]
version: "5.0+"
retrieval_hint: "Bun runtime Node.js alternative TypeScript file I/O SQLite HTTP server test runner"
last_verified: "2026-05-25"
confidence: "high"
---

# Bun Runtime — Key Patterns and Differences from Node.js

## When to Use
- New TypeScript projects where you want zero-config TypeScript execution (no ts-node, no tsx)
- Projects that need fast package installation (bun install is 10-30x faster than npm)
- Simple HTTP APIs, file processing, and scripting where Bun's built-in APIs replace external deps
- Running tests with Bun's built-in Jest-compatible test runner
- NOT when you need full Node.js ecosystem compatibility (some native modules don't work)

## Standard Pattern

```typescript
// === Bun Project Setup ===
// $ bun init        # Creates package.json, tsconfig.json
// $ bun add express  # Works with npm packages
// $ bun run index.ts # Runs TS directly, no compile step

// === File I/O with Bun.file() ===
import { write, file, $ } from "bun";

// Read a file
const text = await file("data.txt").text();
const json = await file("data.json").json();
const bytes = await file("image.png").arrayBuffer();

// Write a file
await write("output.txt", "Hello from Bun!");

// Shell commands (template literal syntax)
const result = await $`ls -la`;
console.log(result.stdout.toString());

// === HTTP Server with Bun.serve() ===
const server = Bun.serve({
  port: 3000,
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/api/data" && request.method === "GET") {
      return Response.json({ message: "Hello from Bun!" });
    }

    if (url.pathname === "/api/upload" && request.method === "POST") {
      const formData = await request.formData();
      const file = formData.get("file") as File;
      await Bun.write(`uploads/${file.name}`, file);
      return Response.json({ uploaded: file.name });
    }

    // Serve static files
    return new Response(Bun.file(`./public/${url.pathname}`));
  },
});

console.log(`Server running on http://localhost:${server.port}`);

// === SQLite with bun:sqlite (built-in, no deps) ===
import { Database } from "bun:sqlite";

const db = new Database("app.db");
db.run(`CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE
)`);

const insert = db.prepare("INSERT INTO users (name, email) VALUES ($name, $email)");
insert.run({ $name: "Alice", $email: "alice@example.com" });

const users = db.prepare("SELECT * FROM users").all();
console.log(users); // Array of typed objects

// === Bun Test Runner (Jest-compatible) ===
// $ bun test
import { describe, test, expect, beforeEach, mock } from "bun:test";

describe("math", () => {
  test("addition", () => {
    expect(1 + 2).toBe(3);
  });
});

// Mocking (built-in)
const fetchMock = mock(() => Response.json({ ok: true }));
const response = await fetchMock("/api");
expect(response.status).toBe(200);
```

## Common Mistakes

```typescript
// WRONG: Assuming all Node.js APIs work identically
// process.env vs Bun.env
// Node: process.env.MY_VAR
// Bun: Bun.env.MY_VAR (also works: process.env.MY_VAR — compatibility layer)
// But process.cwd() works fine.

// WRONG: Using Node.js-specific built-in modules that Bun doesn't support
// Bun supports most Node builtins, but some don't work:
// - child_process (works but bun.spawn is preferred)
// - cluster (NOT supported — Bun uses --cluster mode)
// - async_hooks (partial support)

// CORRECT: Use Bun-native APIs for best performance
import { spawn } from "bun"; // instead of child_process
const proc = spawn(["echo", "hello"]);
const output = await new Response(proc.stdout).text();

// WRONG: Expecting npm resolution to be identical
// Bun uses a different module resolution strategy:
// - It installs packages to ~/.bun/install/cache/
// - Symlinks to node_modules/
// - Some edge cases with deeply nested deps

// WRONG: Using __dirname and __filename in ESM
// In Bun, everything is ESM by default

// CORRECT: Use import.meta equivalents
const thisDir = import.meta.dir;  // __dirname equivalent
const thisFile = import.meta.path;  // __filename equivalent
const thisUrl = import.meta.url;   // file:// URL

// CORRECT: For CommonJS modules, use .cjs extension
// Or use Bun's compat layer: const __dirname = import.meta.dir;
```

## Gotchas
- **Windows support is still evolving:** While Bun works on Windows, some native APIs (especially file watching and process spawning) have rough edges. Check the current release notes for Windows status before committing.
- **Bun.file() is NOT fs.readFileSync():** `Bun.file()` returns a lazy `BunFile` — it doesn't read the file until you call `.text()`, `.json()`, etc. This is more memory-efficient but you must `await` the accessors.
- **Mixed module resolution:** Bun supports both ESM and CommonJS, but mixing them can cause issues. If a package uses `require()`, Bun handles it, but packages that dynamically resolve paths with `__dirname` in ESM will break.
- **Bun's SQLite is synchronous:** Unlike most Bun APIs, `bun:sqlite` operations are synchronous. Don't wrap them in `await` — it won't help. For async wrappers, use `Bun.sleep(0)` to yield between operations.
- **Hot reload with `--hot`:** Bun supports hot module replacement with `bun --hot run file.ts`. But it only works for module-level code, not for server state (e.g., in-memory caches are lost). For servers, use `bun --watch` for full restarts.

## Related
- typescript/runtime/node/fs.md
- typescript/runtime/node/http.md
- typescript-runtime-node-fs
