---
id: "typescript-stdlib-generics"
title: "TypeScript Generics and Utility Types"
language: "typescript"
category: "stdlib"
subcategory: "typing"
tags: ["generics", "utility-types", "type-narrowing", "conditional-types"]
version: "5.0+"
retrieval_hint: "TypeScript generics utility types conditional narrowing"
last_verified: "2026-05-24"
confidence: "high"
---

# TypeScript Generics and Utility Types

## When to Use
- Creating reusable, type-safe functions and classes
- Working with collections of unknown types
- Building type-safe APIs
- Utility types for transformations

## Standard Pattern

```typescript
// Generic function
function first<T>(items: T[]): T | undefined {
  return items[0];
}

const num = first([1, 2, 3]);  // number | undefined
const str = first(['a', 'b']);  // string | undefined

// Generic with constraints
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// Generic class
class Stack<T> {
  private items: T[] = [];

  push(item: T): void {
    this.items.push(item);
  }

  pop(): T | undefined {
    return this.items.pop();
  }
}

// Utility types
type Partial<T> = { [P in keyof T]?: T[P] };
type Required<T> = { [P in keyof T]-?: T[P] };
type Pick<T, K extends keyof T> = { [P in K]: T[P] };
type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;
type Record<K extends keyof any, T> = { [P in K]: T };

// Usage
interface User {
  id: number;
  name: string;
  email: string;
  age: number;
}

type UserUpdate = Partial<User>;  // All fields optional
type UserSummary = Pick<User, 'id' | 'name'>;  // Only id and name
type UserWithoutEmail = Omit<User, 'email'>;  // Everything except email
type UserMap = Record<number, User>;  // { [id: number]: User }

// Conditional types
type IsString<T> = T extends string ? true : false;
type A = IsString<string>;  // true
type B = IsString<number>;  // false

// Mapped types
type Readonly<T> = { readonly [P in keyof T]: T[P] };
type Nullable<T> = { [P in keyof T]: T[P] | null };
```

## Common Mistakes

```typescript
// WRONG: Using any instead of generic
function first(items: any[]): any {
  return items[0];  // No type safety!
}

// CORRECT: Use generic
function first<T>(items: T[]): T | undefined {
  return items[0];
}

// WRONG: Over-constraining generic
function merge<T extends object>(a: T, b: T): T {
  return { ...a, ...b };  // T must be same type!

// CORRECT: Use separate generics
function merge<A extends object, B extends object>(a: A, b: B): A & B {
  return { ...a, ...b } as A & B;
}

// WRONG: Forgetting constraint on generic parameter
function getLength<T>(item: T): number {
  return item.length;  // Error: 'T' has no property 'length'
}

// CORRECT: Constrain T to types with length
function getLength<T extends { length: number }>(item: T): number {
  return item.length;
}
```

## Gotchas
- `T extends U` constrains T to be assignable to U
- `keyof T` extracts keys of type T as a union
- `T[K]` accesses the type of property K on T
- `Partial<T>` makes all properties optional
- `Pick<T, K>` selects specific properties
- `Omit<T, K>` removes specific properties
- `Record<K, V>` creates an object type with keys K and values V

## Related
- typescript/stdlib/error-handling.md
- typescript/stdlib/async-patterns.md
