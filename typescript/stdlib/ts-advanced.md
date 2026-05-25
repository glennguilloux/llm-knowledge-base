---
id: "typescript-stdlib-ts-advanced"
title: "TypeScript Advanced Types"
language: "typescript"
category: "stdlib"
tags: ["types", "conditional", "mapped", "template-literal", "declaration", "module-augmentation"]
version: "5.0+"
retrieval_hint: "TypeScript advanced types conditional mapped template literal declaration module augmentation"
last_verified: "2026-05-24"
confidence: "high"
---

# TypeScript Advanced Types

## When to Use
- Building type-safe utility libraries
- Creating flexible API client types
- Extending third-party library types
- Writing declaration files for JS libraries

## Standard Pattern

```typescript
// --- Conditional types ---
type IsString<T> = T extends string ? true : false;
type A = IsString<string>;  // true
type B = IsString<number>;  // false

type UnwrapPromise<T> = T extends Promise<infer U> ? U : T;
type C = UnwrapPromise<Promise<string>>;  // string
type D = UnwrapPromise<number>;           // number

// --- Mapped types ---
type Readonly<T> = { readonly [K in keyof T]: T[K] };
type Partial<T> = { [K in keyof T]?: T[K] };

type User = { id: number; name: string; email: string };
type ReadonlyUser = Readonly<User>;    // { readonly id: number; ... }
type PartialUser = Partial<User>;      // { id?: number; ... }

// Pick and omit
type UserBasic = Pick<User, "id" | "name">;       // { id: number; name: string }
type UserWithoutEmail = Omit<User, "email">;       // { id: number; name: string }

// --- Template literal types ---
type EventName = "click" | "hover" | "focus";
type HandlerName = `on${Capitalize<EventName>}`;  // "onClick" | "onHover" | "onFocus"

type CSSProperty = "margin" | "padding";
type CSSDirection = "top" | "right" | "bottom" | "left";
type CSSKey = `${CSSProperty}-${CSSDirection}`;  // "margin-top" | "margin-right" | ...

// --- Discriminated unions ---
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "rectangle"; width: number; height: number }
  | { kind: "triangle"; base: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      return Math.PI * shape.radius ** 2;
    case "rectangle":
      return shape.width * shape.height;
    case "triangle":
      return (shape.base * shape.height) / 2;
  }
}

// --- Declaration files ---
// types/my-lib.d.ts
declare module "my-lib" {
  export function process(input: string): number;
  export interface Config {
    debug: boolean;
    timeout: number;
  }
}

// --- Module augmentation ---
declare module "express" {
  interface Request {
    userId?: string;
    requestId?: string;
  }
}

// --- Type predicates ---
function isUser(obj: unknown): obj is User {
  return (
    typeof obj === "object" &&
    obj !== null &&
    "id" in obj &&
    "name" in obj &&
    "email" in obj
  );
}

// Usage
function processInput(input: unknown) {
  if (isUser(input)) {
    console.log(input.name);  // TypeScript knows it's User
  }
}

// --- const assertions ---
const ROUTES = {
  home: "/",
  users: "/users",
  api: "/api",
} as const;

type Route = (typeof ROUTES)[keyof typeof ROUTES];  // "/" | "/users" | "/api"
```

## Common Mistakes

```typescript
// WRONG: Using `any` everywhere
function process(data: any): any {  // No type safety!
  return data.whatever;
}

// CORRECT: Use generics or unknown
function process<T>(data: T): T {
  return data;
}

// WRONG: Non-null assertion without checking
const user = getUser(id)!;  // Runtime crash if null

// CORRECT: Check for null
const user = getUser(id);
if (!user) throw new Error("User not found");

// WRONG: Type assertion that lies
const data = response as User;  // response might not be User!

// CORRECT: Validate with type guard
if (isUser(response)) {
  const user = response;  // Safe
}

// WRONG: Declaration file with any
declare module "my-lib" {
  export function process(data: any): any;  // Defeats the purpose
}

// CORRECT: Specific types
declare module "my-lib" {
  export function process(data: string): number;
}
```

## Gotchas
- `infer` in conditional types captures the type — use it for unwrapping Promises, Arrays, etc.
- Mapped types with `-?` make properties required: `{ [K in keyof T]-?: T[K] }`
- Template literal types are resolved at compile time — no runtime overhead
- Discriminated unions enable exhaustive switch — TypeScript errors if a case is missing
- `as const` creates literal types — `"hello"` instead of `string`
- Module augmentation merges with existing types — be careful with name collisions
- Type predicates (`x is T`) narrow types in if blocks — use for runtime validation

## Related
- typescript/stdlib/generics.md
- typescript/stdlib/error-handling.md
