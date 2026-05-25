---
id: "typescript-stdlib-error-handling"
title: "TypeScript Error Handling"
language: "typescript"
category: "patterns"
subcategory: "error-handling"
tags: ["error", "exception", "result", "error-handling", "try-catch"]
version: "5.0+"
retrieval_hint: "TypeScript error handling result pattern try catch"
last_verified: "2026-05-24"
confidence: "high"
---

# TypeScript Error Handling

## When to Use
- Handling runtime errors gracefully
- Typed error handling (Result pattern)
- API error responses
- Custom error classes

## Standard Pattern

```typescript
// Custom error classes
class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500,
  ) {
    super(message);
    this.name = 'AppError';
  }
}

class NotFoundError extends AppError {
  constructor(resource: string, id: string | number) {
    super(`${resource} with id '${id}' not found`, 'NOT_FOUND', 404);
    this.name = 'NotFoundError';
  }
}

class ValidationError extends AppError {
  constructor(
    public readonly field: string,
    message: string,
  ) {
    super(`Validation error on '${field}': ${message}`, 'VALIDATION_ERROR', 400);
    this.name = 'ValidationError';
  }
}

// Result pattern (functional error handling)
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

function parseJSON<T>(json: string): Result<T> {
  try {
    const data = JSON.parse(json) as T;
    return { success: true, data };
  } catch (error) {
    return { success: false, error: error as Error };
  }
}

// Usage
const result = parseJSON<User>('{"name":"Alice"}');
if (result.success) {
  console.log(result.data.name);  // TypeScript knows data exists
} else {
  console.error(result.error.message);
}

// Error handling with async
async function fetchUser(id: number): Promise<Result<User>> {
  try {
    const response = await fetch(`/api/users/${id}`);
    if (!response.ok) {
      throw new NotFoundError('User', id);
    }
    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    return { success: false, error: error as Error };
  }
}
```

## Common Mistakes

```typescript
// WRONG: Catching generic Error
try {
  riskyOperation();
} catch (error) {
  console.log(error.message);  // Property 'message' does not exist on type 'unknown'
}

// CORRECT: Type narrow the error
try {
  riskyOperation();
} catch (error) {
  if (error instanceof Error) {
    console.log(error.message);
  } else {
    console.log('Unknown error', error);
  }
}

// WRONG: Throwing strings
throw 'Something went wrong';  // No stack trace!

// CORRECT: Throw Error objects
throw new Error('Something went wrong');
throw new AppError('Something went wrong', 'INTERNAL_ERROR');

// WRONG: Swallowing errors silently
try {
  riskyOperation();
} catch {
  // Nothing here — error swallowed, bugs hide forever
}

// CORRECT: Always log or rethrow
try {
  riskyOperation();
} catch (error) {
  logger.error('riskyOperation failed', { error });
  throw error;
}
```

## Gotchas
- TypeScript's `catch` clause types error as `unknown` by default
- Use `instanceof` to narrow error types
- Result pattern avoids try/catch and makes errors explicit in types
- `error` in catch block is always `unknown` in strict mode
- Custom error classes must set `this.name` for proper `instanceof` checks
- Use `never` return type for functions that always throw

## Related
- typescript/stdlib/generics.md
- typescript/web/nextjs/app-router.md
