---
id: "typescript-stdlib-async-patterns"
title: "TypeScript Async/Await Patterns"
language: "typescript"
category: "stdlib"
subcategory: "async"
tags: ["async", "await", "promise", "concurrency", "parallel"]
version: "5.0+"
retrieval_hint: "TypeScript async await promise concurrency parallel"
last_verified: "2026-05-22"
confidence: "high"
---

# TypeScript Async/Await Patterns

## When to Use
- Asynchronous operations (HTTP requests, file I/O, database queries)
- Concurrent execution of independent tasks
- Error handling in async code
- Promise-based APIs

## Standard Pattern

```typescript
// Basic async function
async function fetchData(url: string): Promise<ResponseData> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json();
}

// Parallel execution
async function fetchMultiple(urls: string[]): Promise<ResponseData[]> {
  const promises = urls.map(url => fetchData(url));
  return Promise.all(promises);
}

// Sequential execution
async function processSequentially(items: Item[]): Promise<Result[]> {
  const results: Result[] = [];
  for (const item of items) {
    const result = await processItem(item);
    results.push(result);
  }
  return results;
}

// Error handling
async function safeFetch(url: string): Promise<ResponseData | null> {
  try {
    return await fetchData(url);
  } catch (error) {
    if (error instanceof Error) {
      console.error(`Failed to fetch ${url}: ${error.message}`);
    }
    return null;
  }
}

// Promise.allSettled for partial failures
async function fetchWithFallbacks(urls: string[]): Promise<ResponseData[]> {
  const results = await Promise.allSettled(urls.map(url => fetchData(url)));
  return results
    .filter((r): r is PromiseFulfilledResult<ResponseData> => r.status === 'fulfilled')
    .map(r => r.value);
}

// Async iteration
async function* streamItems(url: string): AsyncGenerator<Item> {
  let page = 1;
  while (true) {
    const response = await fetch(`${url}?page=${page}`);
    const items: Item[] = await response.json();
    if (items.length === 0) break;
    yield* items;
    page++;
  }
}

// Usage
for await (const item of streamItems('/api/items')) {
  console.log(item);
}
```

## Common Mistakes

```typescript
// WRONG: Not awaiting async function
async function getData(): Promise<Data> {
  return fetch('/api/data');  // Returns Promise<Response>, not Data!
}

// CORRECT: Await the fetch
async function getData(): Promise<Data> {
  const response = await fetch('/api/data');
  return response.json();
}

// WRONG: Sequential when parallel is possible
async function processAll(items: Item[]) {
  const results = [];
  for (const item of items) {
    results.push(await process(item));  // Slow! One at a time.
  }
  return results;
}

// CORRECT: Parallel execution
async function processAll(items: Item[]) {
  return Promise.all(items.map(item => process(item)));
}

// WRONG: Swallowing errors
async function risky(): Promise<void> {
  try {
    await dangerousOperation();
  } catch {
    // Silently swallowed!
  }
}

// CORRECT: Handle or rethrow
async function risky(): Promise<void> {
  try {
    await dangerousOperation();
  } catch (error) {
    logger.error('Operation failed', error);
    throw error;
  }
}
```

## Gotchas
- `async` functions always return a `Promise`
- `await` can only be used inside `async` functions
- `Promise.all()` fails fast on first rejection
- `Promise.allSettled()` waits for all, returns status per promise
- Use `for await...of` for async iterables
- `Promise.race()` returns first settled (fulfilled or rejected)
- Always handle errors in async code to avoid unhandled rejections

## Real-World Example

### Parallel Pipeline: Fetch → Transform → Save with Error Isolation

```typescript
interface PipelineResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

async function processBatch<T, R>(
  items: T[],
  transform: (item: T) => Promise<R>,
  concurrency: number = 5
): Promise<PipelineResult<R>[]> {
  const results: PipelineResult<R>[] = [];
  const queue = [...items];
  const workers = Array.from({ length: Math.min(concurrency, queue.length) }, () =>
    (async () => {
      while (queue.length > 0) {
        const item = queue.shift()!;
        try {
          const data = await transform(item);
          results.push({ success: true, data });
        } catch (error) {
          results.push({
            success: false,
            error: error instanceof Error ? error.message : String(error),
          });
        }
      }
    })()
  );
  await Promise.all(workers);
  return results;
}

// Usage: Process 100 URLs concurrently, 10 at a time
async function main() {
  const urls = Array.from({ length: 100 }, (_, i) => `https://api.example.com/items/${i}`);
  const results = await processBatch(urls, async (url) => {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }, 10);

  const succeeded = results.filter((r) => r.success).length;
  const failed = results.filter((r) => !r.success).length;
  console.log(`Done: ${succeeded} OK, ${failed} failed`);
}
```

## Related
- typescript/stdlib/error-handling.md
- typescript/runtime/node/http.md
