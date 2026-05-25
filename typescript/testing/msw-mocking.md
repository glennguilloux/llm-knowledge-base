---
id: "typescript-testing-msw-mocking"
title: "Mock Service Worker (MSW) for API Mocking"
language: "typescript"
category: "testing"
subcategory: "mocking"
tags: ["msw", "mock", "api", "service-worker", "testing", "intercept"]
version: "5.0+"
retrieval_hint: "MSW Mock Service Worker API mocking intercept handlers setup browser node"
last_verified: "2026-05-24"
confidence: "high"
---

# Mock Service Worker (MSW) for API Mocking

## When to Use
- Unit/integration tests that call APIs (no real server needed)
- Frontend development without a running backend
- Testing error scenarios (500s, timeouts, network failures)
- Consistent test data across test runs

## Standard Pattern

```typescript
// --- src/mocks/handlers.ts: Define API handlers ---
import { http, HttpResponse, delay } from "msw";

export const handlers = [
  // GET /api/users
  http.get("/api/users", async () => {
    await delay(150);  // Simulate network latency
    return HttpResponse.json([
      { id: 1, name: "Alice", email: "alice@test.com" },
      { id: 2, name: "Bob", email: "bob@test.com" },
    ]);
  }),

  // GET /api/users/:id
  http.get("/api/users/:id", ({ params }) => {
    const { id } = params;
    return HttpResponse.json({ id: Number(id), name: "Alice", email: "alice@test.com" });
  }),

  // POST /api/users
  http.post("/api/users", async ({ request }) => {
    const body = (await request.json()) as { name: string; email: string };
    return HttpResponse.json({ id: 3, ...body }, { status: 201 });
  }),

  // Error scenario
  http.get("/api/error", () => {
    return HttpResponse.json({ error: "Server error" }, { status: 500 });
  }),
];

// --- src/mocks/browser.ts: For browser (development) ---
import { setupWorker } from "msw/browser";
import { handlers } from "./handlers";

export const worker = setupWorker(...handlers);

// --- src/mocks/server.ts: For tests (Node.js) ---
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);

// --- Vitest setup: tests/setup.ts ---
import { beforeAll, afterEach, afterAll } from "vitest";
import { server } from "../src/mocks/server";

beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// --- Test usage ---
import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../mocks/server";
import { UserList } from "./UserList";

test("renders user list", async () => {
  render(<UserList />);

  await waitFor(() => {
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
  });
});

test("handles API error", async () => {
  server.use(
    http.get("/api/users", () => {
      return HttpResponse.json({ error: "Failed" }, { status: 500 });
    })
  );

  render(<UserList />);

  await waitFor(() => {
    expect(screen.getByText(/error/i)).toBeInTheDocument();
  });
});

test("handles network failure", async () => {
  server.use(
    http.get("/api/users", () => {
      return HttpResponse.error();
    })
  );

  render(<UserList />);

  await waitFor(() => {
    expect(screen.getByText(/network error/i)).toBeInTheDocument();
  });
});
```

## Common Mistakes

```typescript
// WRONG: Not resetting handlers between tests
test("test 1", () => { ... });
test("test 2", () => {
  // test 1's handler overrides are still active!
});

// CORRECT: Reset handlers in afterEach
afterEach(() => server.resetHandlers());

// WRONG: Using server.use() without cleanup
test("error test", () => {
  server.use(http.get("/api/users", () => HttpResponse.error()));
  // Error handler leaks into next test!
});

// CORRECT: server.use() is automatically cleaned up by resetHandlers()
test("error test", () => {
  server.use(http.get("/api/users", () => HttpResponse.error()));
  // resetHandlers() in afterEach removes this override

// WRONG: Mocking at the wrong level
vi.mock("./api", () => ({ fetchUsers: vi.fn() }));  // Mocking the module

// CORRECT: Mock at the network level with MSW
server.use(http.get("/api/users", () => HttpResponse.json([])));

// WRONG: Not awaiting async operations
render(<UserList />);
expect(screen.getByText("Alice")).toBeInTheDocument();  // Data hasn't loaded!

// CORRECT: Use waitFor for async rendering
render(<UserList />);
await waitFor(() => {
  expect(screen.getByText("Alice")).toBeInTheDocument();
});
```

## Gotchas
- `setupServer()` is for Node.js (tests); `setupWorker()` is for browser (development)
- `server.use()` adds handlers that override defaults — cleaned up by `resetHandlers()`
- `HttpResponse.error()` simulates a network failure (no response)
- `HttpResponse.json()` can set status codes: `HttpResponse.json(data, { status: 404 })`
- `delay(ms)` simulates network latency — useful for testing loading states
- MSW intercepts at the network level — your code doesn't need to know about mocks
- Use `onUnhandledRequest: "warn"` to catch API calls you forgot to mock
- MSW v2 uses `http.get/post` instead of `rest.get/post` (v1 API)

## Related
- typescript/testing/playwright-e2e.md
- typescript/testing/react-testing-library.md
- typescript/web/react/forms.md
