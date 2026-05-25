---
id: "typescript-web-zod-validation"
title: "Zod Validation Patterns"
language: "typescript"
category: "web"
subcategory: "validation"
tags: ["zod", "validation", "schema", "type", "inference", "form", "api"]
version: "5.0+"
retrieval_hint: "Zod validation schema type inference parse safeParse form API"
last_verified: "2026-05-24"
confidence: "high"
---

# Zod Validation Patterns

## When to Use
- Validating API request bodies at the server boundary
- Form validation with type-safe error messages
- Environment variable validation at startup
- Inferring TypeScript types from validation schemas (single source of truth)

## Standard Pattern

```typescript
import { z } from "zod";

// --- Schema definition ---
const UserSchema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  email: z.string().email("Invalid email format"),
  age: z.number().int().min(0).max(150).optional(),
  role: z.enum(["admin", "user", "viewer"]).default("user"),
  tags: z.array(z.string()).min(1).default([]),
  address: z.object({
    street: z.string(),
    city: z.string(),
    zip: z.string().regex(/^\d{5}$/, "Invalid zip code"),
  }).optional(),
});

// Infer TypeScript type from schema
type User = z.infer<typeof UserSchema>;

// --- Parsing ---
const result = UserSchema.safeParse(data);
if (result.success) {
  const user: User = result.data;  // Fully typed
} else {
  console.error(result.error.flatten());
}

// Throws on failure
const user = UserSchema.parse(data);

// --- API validation middleware ---
function validateBody<T extends z.ZodType>(schema: T) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      return res.status(400).json({
        error: "Validation failed",
        fields: result.error.flatten().fieldErrors,
      });
    }
    req.body = result.data;
    next();
  };
}

app.post("/api/users", validateBody(UserSchema), (req, res) => {
  const user = req.body;  // Typed as User
  res.json(user);
});

// --- Environment validation ---
const EnvSchema = z.object({
  DATABASE_URL: z.string().url(),
  REDIS_URL: z.string().url().default("redis://localhost:6379"),
  PORT: z.coerce.number().default(3000),
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
});

const env = EnvSchema.parse(process.env);

// --- Form validation with react-hook-form ---
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

const LoginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

function LoginForm() {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(LoginSchema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register("email")} />
      {errors.email && <span>{errors.email.message}</span>}
      <input type="password" {...register("password")} />
      {errors.password && <span>{errors.password.message}</span>}
    </form>
  );
}

// --- Refinements and transforms ---
const PasswordSchema = z.object({
  password: z.string().min(8),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

const DateString = z.string().transform((str) => new Date(str));
```

## Common Mistakes

```typescript
// WRONG: Defining types separately from validation
interface User {
  name: string;
  email: string;
}
const UserSchema = z.object({ name: z.string(), email: z.string() });
// Two sources of truth — can diverge!

// CORRECT: Infer type from schema
const UserSchema = z.object({ name: z.string(), email: z.string() });
type User = z.infer<typeof UserSchema>;

// WRONG: Using parse() without try/catch
const user = UserSchema.parse(data);  // Throws uncaught exception

// CORRECT: Use safeParse() for user input
const result = UserSchema.safeParse(data);
if (!result.success) {
  return res.status(400).json(result.error.flatten());
}

// WRONG: Not handling nested validation errors
const result = schema.safeParse(data);
if (!result.success) {
  console.log(result.error.message);  // Single string, not helpful

// CORRECT: Use flatten() for structured errors
const { fieldErrors, formErrors } = result.error.flatten();
// fieldErrors: { email: ["Invalid email"], name: ["Required"] }

// WRONG: z.string() allows empty strings
z.string().parse("");  // Returns "" — may not be desired

// CORRECT: Use min(1) for non-empty
z.string().min(1, "Required");
```

## Gotchas
- `z.infer<typeof Schema>` gives you the TypeScript type — no need to define interfaces separately
- `safeParse()` returns `{ success, data, error }` — never throws
- `parse()` throws `ZodError` on failure — use `safeParse()` for user input
- `z.coerce.number()` converts string input to number (useful for query params)
- `.optional()` makes the field `T | undefined`; `.nullable()` makes it `T | null`
- `.default(value)` sets a default when the field is missing
- `.transform()` runs after validation — use for data conversion
- `.refine()` adds custom validation that Zod can't express with built-in methods

## Real-World Example

### End-to-End Validation: Schema → API → Form

```typescript
import { z } from "zod";

// Shared schema used by both frontend form and backend API
export const RegistrationSchema = z
  .object({
    email: z.string().email("Invalid email address"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Must contain an uppercase letter")
      .regex(/[0-9]/, "Must contain a number"),
    confirmPassword: z.string(),
    role: z.enum(["user", "admin"]).default("user"),
    metadata: z.record(z.string()).optional(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

export type RegistrationInput = z.infer<typeof RegistrationSchema>;

// API route handler
export async function POST(request: Request) {
  const body = await request.json();
  const result = RegistrationSchema.safeParse(body);
  if (!result.success) {
    return Response.json(
      { errors: result.error.flatten().fieldErrors },
      { status: 422 }
    );
  }
  const user = await createUser(result.data);
  return Response.json({ id: user.id }, { status: 201 });
}

// Frontend form validation (same schema!)
function validateField(field: string, value: unknown) {
  const result = RegistrationSchema.shape[field]?.safeParse(value);
  return result?.success ? null : result?.error.errors[0]?.message;
}
```

## Related
- typescript/web/react/forms.md
- typescript/web/express/middleware.md
- typescript/web/nextjs/app-router.md
