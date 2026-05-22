---
id: "antipatterns-typescript"
title: "TypeScript Anti-Patterns"
language: "typescript"
category: "anti-patterns"
tags: ["antipatterns", "typescript", "common-mistakes", "best-practices"]
version: "n/a"
retrieval_hint: "typescript common mistakes antipatterns any type non-null assertion"
last_verified: "2026-05-22"
confidence: "high"
---

# TypeScript Anti-Patterns

## When to Use
- Reviewing TypeScript code for common mistakes
- Training small LLMs to avoid frequent TypeScript errors
- Code review checklists
- Onboarding developers new to TypeScript

## Standard Pattern

```typescript
// WRONG: Using `any` type (disables all type checking)
function process(data: any): any {
  return data.whatever;  // No type safety at all
}

// CORRECT: Use proper types or unknown
function process(data: unknown): string {
  if (typeof data === "string") return data.toUpperCase();
  throw new Error("Expected string");
}

// WRONG: Non-null assertion operator
const el = document.getElementById("app")!;
el.innerHTML = "hello";  // Crashes if #app doesn't exist

// CORRECT: Check for null
const el = document.getElementById("app");
if (!el) throw new Error("Missing #app element");
el.innerHTML = "hello";

// WRONG: async in useEffect without cleanup
useEffect(async () => {
  const data = await fetchUser(id);
  setUser(data);
}, [id]);  // useEffect callback must not be async

// CORRECT: Use inner async function with cleanup
useEffect(() => {
  let cancelled = false;
  const load = async () => {
    const data = await fetchUser(id);
    if (!cancelled) setUser(data);
  };
  load();
  return () => { cancelled = true; };
}, [id]);

// WRONG: Not handling Promise rejections
async function saveData(data: FormData) {
  await api.save(data);  // Unhandled rejection if it fails
}

// CORRECT: Handle errors explicitly
async function saveData(data: FormData) {
  try {
    await api.save(data);
  } catch (error) {
    toast.error("Save failed");
    throw error;
  }
}

// WRONG: Type assertion escape hatch
const data = JSON.parse(input) as UserData;  // No runtime validation

// CORRECT: Validate at runtime with zod
const UserSchema = z.object({ name: z.string(), age: z.number() });
const data = UserSchema.parse(JSON.parse(input));  // Throws if invalid

// WRONG: Enum abuse (generates runtime code)
enum Direction { Up, Down, Left, Right }

// CORRECT: Use const enum or union type
type Direction = "up" | "down" | "left" | "right";

// WRONG: == instead of === for comparisons
if (value == null) {  // Matches both null and undefined — confusing
  handleMissing();
}

// CORRECT: Use === for strict comparison
if (value === null || value === undefined) {
  handleMissing();
}

// WRONG: Ignoring Promise return (fire-and-forget without error handling)
function handleClick() {
  submitForm(data);  // Returns Promise, errors lost
}

// CORRECT: Handle the Promise
async function handleClick() {
  try {
    await submitForm(data);
  } catch (err) {
    showError(err);
  }
}
```

## Common Mistakes
The most damaging TypeScript anti-patterns are `any` type usage (defeats the entire purpose of TypeScript), non-null assertions (runtime crashes), and unhandled Promise rejections (silent failures). Type assertions without runtime validation give false confidence. Enum generates unnecessary runtime code when union types suffice.

## Gotchas
- `any` disables ALL type checking for that value — it propagates silently
- `unknown` is the type-safe alternative to `any` — forces you to narrow before use
- `!` (non-null assertion) is a compile-time lie — it does not add runtime checks
- `as` type assertions are not validated at runtime
- `interface` is structural, not nominal — duck typing applies
- `enum` generates runtime JavaScript code — `const enum` or union types do not
- `===` checks both value AND type — `==` does coercion
- `void` in Promise means the resolved value is ignored, not that it returns nothing
- Async functions always return a Promise — forgetting to await means silent failure

## Related
- typescript/stdlib/error-handling.md
- typescript/stdlib/generics.md
- typescript/web/react/hooks.md
