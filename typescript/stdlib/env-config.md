---
id: "typescript-stdlib-env-config"
title: "Environment Variables and Config Validation"
language: "typescript"
category: "stdlib"
tags: ["env", "config", "zod", "dotenv", "environment", "validation", "12-factor"]
version: "5.0+"
retrieval_hint: "environment variables config zod dotenv validation 12-factor process.env"
last_verified: "2026-05-24"
confidence: "high"
---

# Environment Variables and Config Validation

## When to Use
- Loading configuration from environment variables
- Validating config at startup (fail fast, not at first request)
- Type-safe access to environment variables
- Managing secrets and environment-specific settings

## Standard Pattern

```typescript
import { z } from "zod";
import "dotenv/config"; // Loads .env file

// --- Define config schema ---
const ConfigSchema = z.object({
  NODE_ENV: z.enum(["development", "staging", "production"]).default("development"),
  PORT: z.coerce.number().int().min(1).max(65535).default(3000),
  DATABASE_URL: z.string().url(),
  REDIS_URL: z.string().url().default("redis://localhost:6379"),
  JWT_SECRET: z.string().min(32),
  LOG_LEVEL: z.enum(["debug", "info", "warn", "error"]).default("info"),
  CORS_ORIGINS: z.string().transform((s) => s.split(",").map((o) => o.trim())),
});

type Config = z.infer<typeof ConfigSchema>;

// --- Parse and validate at startup ---
function loadConfig(): Config {
  const result = ConfigSchema.safeParse(process.env);

  if (!result.success) {
    console.error("Invalid configuration:");
    console.error(result.error.format());
    process.exit(1);  // Fail fast!
  }

  return result.data;
}

export const config = loadConfig();

// --- Usage ---
// import { config } from "./config";
// console.log(config.PORT);           // number (not string!)
// console.log(config.DATABASE_URL);   // string
// console.log(config.CORS_ORIGINS);   // string[]


// --- Type-safe config access ---
// config.NODE_ENV    — "development" | "staging" | "production"
// config.PORT        — number
// config.DATABASE_URL — string (validated URL)
// config.JWT_SECRET  — string (min 32 chars)


// --- .env.example ---
// NODE_ENV=development
// PORT=3000
// DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
// REDIS_URL=redis://localhost:6379
// JWT_SECRET=your-secret-key-at-least-32-chars
// LOG_LEVEL=info
// CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Common Mistakes

```typescript
// WRONG: Accessing process.env without validation
const dbUrl = process.env.DATABASE_URL;  // string | undefined
await connect(dbUrl);  // Type error, may be undefined

// CORRECT: Validate at startup with zod
const config = ConfigSchema.parse(process.env);
await connect(config.DATABASE_URL);  // Always string

// WRONG: No type coercion for numbers
const port = process.env.PORT || "3000";  // string, not number
app.listen(port);  // Works, but port is string

// CORRECT: Use z.coerce.number()
const config = ConfigSchema.parse(process.env);
app.listen(config.PORT);  // number

// WRONG: Not failing fast on missing config
const dbUrl = process.env.DATABASE_URL;  // undefined
// App starts, crashes on first DB query

// CORRECT: Validate at startup, exit on failure
const result = ConfigSchema.safeParse(process.env);
if (!result.success) {
  console.error(result.error.format());
  process.exit(1);
}

// WRONG: Hardcoded secrets
const JWT_SECRET = "super-secret-key-12345678901234567890";

// CORRECT: From environment
const config = loadConfig();
const JWT_SECRET = config.JWT_SECRET;

// WRONG: .env committed to git
// CORRECT: .env in .gitignore, .env.example committed

// WRONG: Parsing comma-separated values manually
const origins = process.env.CORS_ORIGINS?.split(",") || [];

// CORRECT: Use zod transform
CORS_ORIGINS: z.string().transform((s) => s.split(",").map((o) => o.trim())),
```

## Gotchas
- `process.env` values are always `string | undefined` — use zod for type coercion
- `z.coerce.number()` converts "3000" to 3000 automatically
- `.env` files should be in `.gitignore` — commit `.env.example` with placeholder values
- `dotenv/config` does NOT override existing env vars — env vars take precedence
- Validate config at startup, not lazily — fail fast with clear error messages
- `z.string().url()` validates URL format — catches typos early
- Use `z.enum()` for restricted values — prevents typos in environment names

## Related
- typescript/web/express-server.md
- typescript/stdlib/error-handling.md
