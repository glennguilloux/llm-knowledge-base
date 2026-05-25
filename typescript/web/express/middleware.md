---
id: "typescript-web-express-middleware"
title: "Express Middleware Chains and Error Handling"
language: "typescript"
category: "web"
subcategory: "backend"
tags: ["express", "middleware", "error-handling", "routing", "auth", "chain"]
version: "5.0+"
retrieval_hint: "Express middleware chain error handling NextFunction router auth"
last_verified: "2026-05-24"
confidence: "high"
---

# Express Middleware Chains and Error Handling

## When to Use
- Building REST APIs with Node.js
- Request processing pipeline (auth, validation, logging)
- Error handling middleware for centralized error responses
- Route organization with Express Router

## Standard Pattern

```typescript
import express, { Request, Response, NextFunction, Router } from "express";

const app = express();

// --- Built-in middleware ---
app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true }));

// --- Logging middleware ---
function requestLogger(req: Request, _res: Response, next: NextFunction) {
  console.log(`${req.method} ${req.path}`);
  next();
}
app.use(requestLogger);

// --- Auth middleware ---
function authenticate(req: Request, res: Response, next: NextFunction) {
  const token = req.headers.authorization?.replace("Bearer ", "");
  if (!token) {
    return res.status(401).json({ error: "No token provided" });
  }
  try {
    const payload = verifyJwt(token);
    req.user = payload;
    next();
  } catch {
    res.status(401).json({ error: "Invalid token" });
  }
}

function requireRole(...roles: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({ error: "Insufficient permissions" });
    }
    next();
  };
}

// --- Router organization ---
const userRouter = Router();

userRouter.get("/", listUsers);
userRouter.get("/:id", getUser);
userRouter.post("/", authenticate, requireRole("admin"), createUser);
userRouter.put("/:id", authenticate, updateUser);
userRouter.delete("/:id", authenticate, requireRole("admin"), deleteUser);

app.use("/api/users", userRouter);

// --- Error handling middleware (must have 4 params) ---
function errorHandler(err: Error, req: Request, res: Response, _next: NextFunction) {
  console.error(`Error: ${err.message}`, { path: req.path, stack: err.stack });

  if (err instanceof ValidationError) {
    return res.status(400).json({ error: err.message, fields: err.fields });
  }
  if (err instanceof NotFoundError) {
    return res.status(404).json({ error: err.message });
  }

  res.status(500).json({ error: "Internal server error" });
}

app.use(errorHandler);

// --- Async wrapper (catches async errors) ---
function asyncHandler(fn: (req: Request, res: Response, next: NextFunction) => Promise<void>) {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

app.get("/api/data", asyncHandler(async (req, res) => {
  const data = await fetchData();  // If this throws, error handler catches it
  res.json(data);
}));
```

## Common Mistakes

```typescript
// WRONG: Calling next() after sending response
app.get("/api/data", (req, res, next) => {
  res.json({ data: 1 });
  next();  // Runs next middleware after response sent!
});

// CORRECT: Either send response OR call next(), not both
app.get("/api/data", (req, res) => {
  res.json({ data: 1 });
});

// WRONG: Error handler missing 4th parameter (won't catch errors)
app.use((err, req, res) => {  // Missing next!
  res.status(500).json({ error: err.message });
});

// CORRECT: Error handler must have exactly 4 parameters
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  res.status(500).json({ error: err.message });
});

// WRONG: Not handling async errors
app.get("/api/data", async (req, res) => {
  const data = await fetchData();  // Unhandled promise rejection!
  res.json(data);
});

// CORRECT: Wrap async handlers
app.get("/api/data", asyncHandler(async (req, res) => {
  const data = await fetchData();
  res.json(data);
}));

// WRONG: Middleware order wrong (error handler before routes)
app.use(errorHandler);
app.get("/api/data", handler);  // Error handler won't catch route errors

// CORRECT: Error handler LAST
app.get("/api/data", handler);
app.use(errorHandler);
```

## Gotchas
- Error handlers MUST have 4 parameters: `(err, req, res, next)` — Express uses this to distinguish them
- `next()` without arguments runs the next regular middleware; `next(err)` runs the error handler
- Middleware order matters — they execute in the order registered
- `express.json()` must be registered before routes that read `req.body`
- Async errors are NOT caught by Express — use `asyncHandler` or Express 5
- `Router()` creates modular route groups — mount with `app.use("/prefix", router)`
- `req.user` is custom — extend the Express `Request` type for TypeScript
- `res.json()` and `res.send()` end the request — don't call both

## Related
- typescript/web/express-server.md
- typescript/web/nextjs/app-router.md
- error-handling/structured-errors.md
