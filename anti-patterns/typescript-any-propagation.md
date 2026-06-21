---
id: "anti-patterns-typescript-any-propagation"
title: "TypeScript Anti-Pattern: any Type Propagation"
language: "typescript"
category: "anti-patterns"
tags: ["antipatterns", "typescript", "any", "type-safety", "type-system"]
version: "n/a"
retrieval_hint: "TypeScript any propagation type safety unknown type narrowing as any cast JSON.parse type guard eslint no-explicit-any"
last_verified: "2026-05-24"
confidence: "high"
---

# TypeScript Anti-Pattern: any Type Propagation

## When to Use
- Reviewing TypeScript code for type safety regressions
- Training LLMs to avoid type-erasing patterns
- Migrating codebases from `any` to proper types
- Understanding the difference between `any` and `unknown`

## Standard Pattern

```typescript
// ---------------------------------------------------------------------------
// WRONG: any cascading through function returns (type poison)
// ---------------------------------------------------------------------------

// WRONG: One any return contaminates all callers
function fetchData(url: string): any {
  return { id: 1, name: "Alice" };
}

const data = fetchData("/api/user");
const name: string = data.name;           // No type checking on data
const result = data.nonExistentMethod();  // No error — runtime crash!

// CORRECT: Proper return type keeps callers safe
interface UserData {
  id: number;
  name: string;
}

function fetchData(url: string): UserData {
  return { id: 1, name: "Alice" };
}

const data = fetchData("/api/user");
const name: string = data.name;                // ✅ OK
const result = data.nonExistentMethod();       // ❌ Compile error

// ---------------------------------------------------------------------------
// WRONG: Using any instead of unknown
// ---------------------------------------------------------------------------

// WRONG: any lets you do anything without checks
function parseConfig(data: any) {
  console.log(data.host);             // No safety — could be undefined
  return data.port * 2;               // Could be NaN (no type checking)
}

// CORRECT: unknown forces type narrowing before use
function parseConfig(data: unknown) {
  // ❌ Cannot access properties on unknown without narrowing
  // console.log(data.host);  // Compile error

  if (isConfig(data)) {
    console.log(data.host);  // ✅ Narrowed, safe
    return data.port * 2;
  }
  throw new Error("Invalid config");
}

function isConfig(obj: unknown): obj is { host: string; port: number } {
  return (
    typeof obj === "object" &&
    obj !== null &&
    "host" in obj &&
    typeof (obj as any).host === "string" &&
    "port" in obj &&
    typeof (obj as any).port === "number"
  );
}

// ---------------------------------------------------------------------------
// WRONG: as any cast to bypass type checking
// ---------------------------------------------------------------------------

// WRONG: Using as any silences real type errors
function saveUser(user: { id: number; name: string }) {
  // ...
}

const raw = { id: "abc", name: "Alice" };
saveUser(raw as any);  // Silently accepts string id — runtime bug!

// CORRECT: Fix the actual type mismatch or use proper conversion
const fixed = { ...raw, id: Number(raw.id) };
saveUser(fixed);

// ---------------------------------------------------------------------------
// WRONG: JSON.parse returning any
// ---------------------------------------------------------------------------

// WRONG: JSON.parse returns any — untyped data poisons everything
const config = JSON.parse(localStorage.getItem("config") || "{}");
console.log(config.database.host);  // Runtime error if host is missing

// CORRECT: Wrap in type-safe parsing
interface AppConfig {
  database: { host: string; port: number };
  logging: { level: string };
}

function loadConfig(): AppConfig {
  const raw = JSON.parse(localStorage.getItem("config") || "{}");
  return validateConfig(raw);
}

function validateConfig(raw: unknown): AppConfig {
  if (typeof raw !== "object" || raw === null) {
    throw new Error("Invalid config format");
  }
  // Full validation omitted for brevity — use zod or similar
  return raw as AppConfig;  // Narrowed to object type first
}

// ---------------------------------------------------------------------------
// WRONG: any[] instead of proper typed arrays
// ---------------------------------------------------------------------------

// WRONG: Using any[] loses all type information
function processItems(items: any[]) {
  return items.map(item => item.value * 2);  // No type safety
}

// CORRECT: Generic typed array
function processItems<T extends { value: number }>(items: T[]): number[] {
  return items.map(item => item.value * 2);
}

// ---------------------------------------------------------------------------
// WRONG: eslint-disable no-explicit-any without justification
// ---------------------------------------------------------------------------

// WRONG: Silencing the linter without fixing the issue
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function legacyAdapter(input: any): any {
  return input;
}

// CORRECT: Use unknown or generics when dealing with external data
function legacyAdapter<T>(input: T): T {
  return input;
}

// ---------------------------------------------------------------------------
// WRONG: Object.keys() and keyof pitfalls
// ---------------------------------------------------------------------------

// WRONG: Object.keys() returns string[], not (keyof T)[]
interface User {
  id: number;
  name: string;
}

function updateUser(user: User, updates: Partial<User>) {
  // ❌ This compiles with as any but loses type safety
  (Object.keys(updates) as (keyof User)[]).forEach(key => {
    user[key] = updates[key]!;  // Assertions needed
  });
}

// CORRECT: Use type-safe Object.keys with explicit cast
function updateUserSafe<T extends object>(
  target: T,
  updates: Partial<T>
): void {
  const keys = Object.keys(updates) as (keyof T)[];
  for (const key of keys) {
    if (updates[key] !== undefined) {
      target[key] = updates[key]!;
    }
  }
}

// ---------------------------------------------------------------------------
// WRONG: any in catch blocks
// ---------------------------------------------------------------------------

// WRONG: catch with any loses error type info
try {
  riskyOperation();
} catch (err: any) {
  console.log(err.message);     // any — could be anything
  console.log(err.statusCode);  // No type checking
}

// CORRECT: Use unknown in catch (TS 4.0+)
try {
  riskyOperation();
} catch (err: unknown) {
  if (err instanceof Error) {
    console.log(err.message);  // ✅ Typed
  } else if (typeof err === "object" && err && "statusCode" in err) {
    const statusCode = (err as { statusCode: number }).statusCode;
    console.log(statusCode);
  }
}
```

## Common Mistakes
The most insidious pattern is `any` propagation: one function returning `any` makes all its callers type-unsafe, and those callers' callers, etc. It's a type-safety poison. Second, using `any` instead of `unknown` — `unknown` forces type narrowing before use, while `any` allows any operation without checking. Third, `as any` casts to bypass legitimate type errors instead of fixing the root cause. Fourth, `JSON.parse` returning `any` is the single most common source of `any` in real codebases.

## Gotchas
- `any` is **contagious** — any value that comes into contact with `any` becomes `any` (function params, return types, array elements)
- `unknown` is the type-safe alternative: you must narrow (typeof, instanceof, custom type guard) before using it
- `as any` disables ALL type checking on that expression — it's a nuclear option, not a type assertion
- `as` type assertions (without `any`) are safer — they just override inference for types you know better
- `JSON.parse()` returns `any` — always wrap in a type guard or use libraries like `zod` or `io-ts` for validation
- `fetch()` response `.json()` also returns `Promise<any>` — same problem
- `any[]` is NOT the same as `unknown[]` — `any[]` allows any operation, `unknown[]` requires narrowing
- `eslint @typescript-eslint/no-explicit-any` catches explicit `any` annotations but NOT inferred `any` — enable `noImplicitAny` in tsconfig too
- `Object.keys()` returns `string[]` because TypeScript doesn't know the object hasn't been extended at runtime
- `catch (err: any)` is the default in older TS — use `useUnknownInCatchVariables: true` in tsconfig for `err: unknown`
- Third-party libraries with `any` in their types propagate into your code — consider wrapping them in typed adapters
- `any` in generic constraints (`T extends any`) is different from `any` as a value — avoid both
- `// eslint-disable-next-line @typescript-eslint/no-explicit-any` should require a justification comment explaining why it's unavoidable

## Related
- anti-patterns/typescript-antipatterns.md
- anti-patterns/javascript-antipatterns.md
