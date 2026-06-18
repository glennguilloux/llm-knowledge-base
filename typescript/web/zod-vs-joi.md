---
id: "typescript-web-zod-vs-joi"
title: "Zod vs Joi — When to Use Which for Validation"
language: "typescript"
category: "web"
subcategory: "validation"
tags: ["zod", "joi", "validation", "schema", "typescript", "comparison", "type-inference"]
version: "5.0+"
retrieval_hint: "Zod Joi validation schema comparison TypeScript type inference runtime"
last_verified: "2026-05-25"
confidence: "high"
---

# Zod vs Joi — When to Use Which for Validation

## When to Use
- **Zod:** TypeScript-first projects where static type inference from schemas eliminates duplication
- **Joi:** Legacy Express/Node.js projects (especially in JavaScript), or when you need rich string/object validators built-in
- **Zod:** Modern stacks (Next.js, tRPC, TanStack Query) where schema = type = validation
- **Joi:** Projects already using @hapi/joi or where you need the mature plugin ecosystem

## Standard Pattern

```typescript
// === Zod ===
import { z } from "zod";

// Schema definition — TYPES ARE INFERRED AUTOMATICALLY
const UserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().positive().optional(),
  role: z.enum(["admin", "user", "guest"]).default("user"),
  tags: z.array(z.string()).max(10).default([]),
});

// Type is inferred — NO separate type definition!
type User = z.infer<typeof UserSchema>;
// Equivalent to:
// { name: string; email: string; age?: number; role: "admin" | "user" | "guest"; tags: string[] }

const result = UserSchema.safeParse(input);
if (!result.success) {
  console.error(result.error.issues);
  // { path: ["email"], message: "Invalid email", code: "invalid_string" }
}

// === Joi ===
import Joi from "joi";

const userJoiSchema = Joi.object({
  name: Joi.string().min(1).max(100).required(),
  email: Joi.string().email().required(),
  age: Joi.number().integer().positive().optional(),
  role: Joi.string().valid("admin", "user", "guest").default("user"),
  tags: Joi.array().items(Joi.string()).max(10).default([]),
});

const joiResult = userJoiSchema.validate(input);
if (joiResult.error) {
  console.error(joiResult.error.details);
  // { path: ["email"], message: "\"email\" must be a valid email", type: "string.email" }
}

// === Practical: User registration endpoint with Zod ===
import { z } from "zod";

const RegisterSchema = z.object({
  username: z.string()
    .min(3, "Username must be at least 3 chars")
    .max(30)
    .regex(/^[a-zA-Z0-9_]+$/, "Only letters, numbers, underscores"),
  email: z.string().email(),
  password: z.string()
    .min(8)
    .regex(/[A-Z]/, "Need uppercase")
    .regex(/[0-9]/, "Need digit"),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type RegisterInput = z.infer<typeof RegisterSchema>;
// That's your type. No interface needed.

function parseRegistration(data: unknown): RegisterInput {
  return RegisterSchema.parse(data); // Throws on invalid
}

// === Practical: Express endpoint with Joi ===
function validateRegistrationJoi(data: unknown) {
  const schema = Joi.object({
    username: Joi.string().alphanum().min(3).max(30).required(),
    email: Joi.string().email().required(),
    password: Joi.string().min(8).pattern(/[A-Z]/).pattern(/[0-9]/).required(),
    confirmPassword: Joi.string().valid(Joi.ref("password")).required()
      .messages({ "any.only": "Passwords don't match" }),
  });

  const { error, value } = schema.validate(data, { abortEarly: false });
  if (error) throw error;
  return value; // Type is any — Joi doesn't infer types
}
```

## Common Mistakes

```typescript
// ZOD MISTAKES:

// WRONG: Duplicating types alongside Zod schemas
interface User {
  name: string;
  email: string;
}
const UserSchema = z.object({
  name: z.string(),
  email: z.string().email(),
});
// Now you maintain TWO definitions — they'll drift

// CORRECT: Infer the type from the schema
const UserSchema = z.object({
  name: z.string(),
  email: z.string().email(),
});
type User = z.infer<typeof UserSchema>; // Single source of truth

// WRONG: Using Zod with discriminated unions — missing discriminator
const ResultSchema = z.union([
  z.object({ status: z.literal("ok"), data: z.any() }),
  z.object({ status: z.literal("err"), error: z.string() }),
]);
// This works but doesn't narrow the discriminated type

// CORRECT: Use z.discriminatedUnion for better type narrowing
const ResultSchema = z.discriminatedUnion("status", [
  z.object({ status: z.literal("ok"), data: z.any() }),
  z.object({ status: z.literal("err"), error: z.string() }),
]);

// JOI MISTAKES:

// WRONG: Using Joi in a TypeScript codebase
const schema = Joi.object({ name: Joi.string() });
const value = schema.validate(input).value;
// value is typed as any — no type safety

// CORRECT: Only use Joi if you're in JavaScript or can't migrate
// If you must use Joi in TS, wrap it with a type assertion
interface NameSchema { name: string; }
const value = schema.validate(input).value as NameSchema;
```

## Gotchas
- **Zod's `.default()` only applies on `.parse()`, not on partial updates:** When using `z.object({ role: z.enum(["a","b"]).default("a") }).partial()`, the default is NOT applied for missing fields. Use `.pipe()` or runtime merging.
- **Joi has richer string validation:** Joi's `Joi.string()` has built-in methods like `.alphanum()`, `.creditCard()`, `.hex()`, `.base64()`, `.isoDate()` that Zod doesn't have natively. In Zod you'd use `.regex()` or `.refine()` with custom logic.
- **Error format differences:** Zod returns `ZodError` with `issues: [{ path, message, code }]`. Joi returns `ValidationError` with `details: [{ path, message, type }]`. If you're switching, your error handling middleware needs updating.
- **Zod's `.refine()` vs Joi's `.custom()`:** Both allow custom validation logic. Zod's `.refine()` returns a boolean (pass/fail) while `.superRefine()` allows granular error reporting. Joi's `.custom()` returns the modified value or throws.
- **tRPC integration:** Zod has FIRST-CLASS tRPC support — `z.string()` maps directly to tRPC types. Joi doesn't integrate with tRPC at all. This alone decides the choice for tRPC projects.

## Related
- typescript/web/zod-validation.md
- typescript/web/trpc-patterns.md
