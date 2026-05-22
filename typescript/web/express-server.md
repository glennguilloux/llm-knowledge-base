---
id: "typescript-web-express-server"
title: "Express/Fastify Server Patterns"
language: "typescript"
category: "web"
tags: ["express", "fastify", "server", "api", "middleware", "routing", "REST"]
version: "5.0+"
retrieval_hint: "express fastify server API middleware routing REST endpoint handler"
last_verified: "2026-05-22"
confidence: "high"
---

# Express/Fastify Server Patterns

## When to Use
- Building REST APIs with TypeScript
- Creating HTTP servers with middleware chains
- Serving web applications with routing
- Building microservices

## Standard Pattern

```typescript
import express, { Request, Response, NextFunction } from "express";
import { z } from "zod";

const app = express();
app.use(express.json());

// --- Type-safe request handling ---
const CreateUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().min(0).max(150),
});

type CreateUser = z.infer<typeof CreateUserSchema>;

interface User {
  id: number;
  name: string;
  email: string;
  age: number;
}

const users: Map<number, User> = new Map();
let nextId = 1;

// --- Validation middleware ---
function validate<T>(schema: z.ZodSchema<T>) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      res.status(400).json({
        error: "Validation failed",
        details: result.error.issues,
      });
      return;
    }
    req.body = result.data;
    next();
  };
}

// --- Routes ---
app.get("/users", (req: Request, res: Response) => {
  const page = parseInt(req.query.page as string) || 1;
  const limit = parseInt(req.query.limit as string) || 10;
  const allUsers = Array.from(users.values());
  const start = (page - 1) * limit;
  res.json({
    data: allUsers.slice(start, start + limit),
    total: allUsers.length,
    page,
    limit,
  });
});

app.post("/users", validate(CreateUserSchema), (req: Request, res: Response) => {
  const user: User = { id: nextId++, ...req.body };
  users.set(user.id, user);
  res.status(201).json(user);
});

app.get("/users/:id", (req: Request, res: Response) => {
  const user = users.get(parseInt(req.params.id));
  if (!user) {
    res.status(404).json({ error: "User not found" });
    return;
  }
  res.json(user);
});

// --- Error handling middleware ---
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error(`Error: ${err.message}`, err);
  res.status(500).json({ error: "Internal server error" });
});

// --- Graceful shutdown ---
const server = app.listen(3000, () => {
  console.log("Server running on port 3000");
});

process.on("SIGTERM", () => {
  console.log("SIGTERM received, shutting down...");
  server.close(() => {
    process.exit(0);
  });
});
```

## Common Mistakes

```typescript
// WRONG: No input validation
app.post("/users", (req, res) => {
  const user = req.body;  // Trusting client input!
  users.set(user.id, user);
});

// CORRECT: Validate with zod
app.post("/users", validate(CreateUserSchema), (req, res) => {
  const user = { id: nextId++, ...req.body };
  users.set(user.id, user);
});

// WRONG: Not handling async errors
app.get("/data", async (req, res) => {
  const data = await fetchData();  // If this throws, server hangs!
  res.json(data);
});

// CORRECT: Wrap async handlers
app.get("/data", async (req, res, next) => {
  try {
    const data = await fetchData();
    res.json(data);
  } catch (err) {
    next(err);
  }
});

// WRONG: Sending response without return
app.get("/users/:id", (req, res) => {
  if (!users.has(req.params.id)) {
    res.status(404).json({ error: "Not found" });  // No return!
  }
  res.json(users.get(req.params.id));  // Also executes!
});

// CORRECT: Return after sending response
app.get("/users/:id", (req, res) => {
  const user = users.get(parseInt(req.params.id));
  if (!user) {
    res.status(404).json({ error: "Not found" });
    return;
  }
  res.json(user);
});

// WRONG: No graceful shutdown
app.listen(3000);  // No cleanup on SIGTERM

// CORRECT: Handle shutdown signals
const server = app.listen(3000);
process.on("SIGTERM", () => {
  server.close(() => process.exit(0));
});
```

## Gotchas
- Express doesn't catch async errors by default — wrap in try/catch or use `express-async-errors`
- `req.body` is `undefined` without `express.json()` middleware
- Route parameters are always strings — parse with `parseInt()` or zod
- Middleware order matters — `express.json()` must be before routes that read `req.body`
- `res.json()` and `res.send()` end the response — don't call them twice
- Use `next(err)` to forward errors to the error handling middleware
- Fastify is faster than Express and has built-in schema validation — consider for new projects

## Related
- typescript/stdlib/error-handling.md
- typescript/stdlib/async-patterns.md
- typescript/web/nextjs/app-router.md
