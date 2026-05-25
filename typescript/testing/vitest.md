---
id: "typescript-testing-vitest"
title: "Vitest Testing Framework"
language: "typescript"
category: "testing"
subcategory: "unit-testing"
tags: ["vitest", "testing", "mock", "describe", "expect", "vi"]
version: "1.0+"
retrieval_hint: "Vitest testing mock describe expect vi.fn"
last_verified: "2026-05-24"
confidence: "high"
---

# Vitest Testing Framework

## When to Use
- Unit testing TypeScript/JavaScript
- Component testing with React/Vue
- Fast test execution with Vite
- ESM-native testing

## Standard Pattern

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Basic test
describe('Calculator', () => {
  it('should add numbers', () => {
    expect(1 + 1).toBe(2);
  });

  it('should handle objects', () => {
    expect({ name: 'Alice' }).toEqual({ name: 'Alice' });
  });
});

// Setup and teardown
describe('UserService', () => {
  let service: UserService;

  beforeEach(() => {
    service = new UserService();
  });

  it('should create user', async () => {
    const user = await service.create({ name: 'Alice' });
    expect(user.name).toBe('Alice');
    expect(user.id).toBeDefined();
  });
});

// Mocking
describe('with mocks', () => {
  it('should mock function', () => {
    const mockFn = vi.fn();
    mockFn('hello');
    expect(mockFn).toHaveBeenCalledWith('hello');
    expect(mockFn).toHaveBeenCalledTimes(1);
  });

  it('should mock module', async () => {
    vi.mock('./api', () => ({
      fetchUsers: vi.fn().mockResolvedValue([{ id: 1, name: 'Alice' }]),
    }));

    const { fetchUsers } = await import('./api');
    const users = await fetchUsers();
    expect(users).toHaveLength(1);
  });

  it('should spy on method', () => {
    const obj = { greet: (name: string) => `Hello, ${name}!` };
    const spy = vi.spyOn(obj, 'greet');
    
    obj.greet('Alice');
    
    expect(spy).toHaveBeenCalledWith('Alice');
    spy.mockRestore();
  });
});

// Async tests
describe('async operations', () => {
  it('should resolve promise', async () => {
    const result = await Promise.resolve(42);
    expect(result).toBe(42);
  });

  it('should reject promise', async () => {
    await expect(Promise.reject(new Error('fail'))).rejects.toThrow('fail');
  });
});

// Type testing
describe('type tests', () => {
  it('should infer types', () => {
    const result = calculate(1, 2);
    expectTypeOf(result).toBeNumber();
  });
});
```

## Common Mistakes

```typescript
// WRONG: Not cleaning up mocks
describe('test suite', () => {
  it('test 1', () => {
    vi.mock('./module');  // Persists to other tests!
  });

  it('test 2', () => {
    // Module still mocked!
  });
});

// CORRECT: Use beforeEach with vi.restoreAllMocks
describe('test suite', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });
});

// WRONG: Testing implementation details
it('should call internal method', () => {
  const spy = vi.spyOn(service, '_internalMethod');
  service.doSomething();
  expect(spy).toHaveBeenCalled();  // Brittle!
});

// CORRECT: Test behavior
it('should return correct result', () => {
  const result = service.doSomething();
  expect(result).toBe('expected');
});

// WRONG: Missing await on async test
it('should fetch user', () => {
  const result = getUser(1);  // Returns a Promise, not a user!
  expect(result.name).toBe('Alice');  // Always passes — Promise has no .name
});

// CORRECT: Await the async call
it('should fetch user', async () => {
  const result = await getUser(1);
  expect(result.name).toBe('Alice');
});
```

## Gotchas
- Vitest is Vite-native — uses same config (vite.config.ts)
- `vi.fn()` creates mock function; `vi.spyOn()` spies on existing
- `vi.mock()` hoists to top of file automatically
- `vi.restoreAllMocks()` resets all mocks
- `expectTypeOf()` for type-level assertions
- Use `vi.stubGlobal()` for global mocks (fetch, localStorage)
- `describe.concurrent` for parallel test execution

## Related
- typescript/testing/vitest.md
- typescript/web/react/hooks.md
