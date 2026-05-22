---
id: "typescript-testing-react-testing-library"
title: "React Testing Library Patterns"
language: "typescript"
category: "testing"
subcategory: "unit-testing"
tags: ["react-testing-library", "rtl", "testing", "render", "screen", "user-event"]
version: "5.0+"
retrieval_hint: "React Testing Library render screen userEvent waitFor getBy queryBy"
last_verified: "2026-05-22"
confidence: "high"
---

# React Testing Library Patterns

## When to Use
- Testing React components in isolation (unit/integration tests)
- Testing user interactions (click, type, submit)
- Testing component rendering and conditional display
- Testing accessibility (components tested as users see them)

## Standard Pattern

```typescript
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// --- Basic render and query ---
test("renders user name", () => {
  render(<UserCard user={{ name: "Alice", email: "alice@test.com" }} />);

  expect(screen.getByText("Alice")).toBeInTheDocument();
  expect(screen.getByText("alice@test.com")).toBeInTheDocument();
});

// --- User interactions ---
test("increments counter on click", async () => {
  const user = userEvent.setup();
  render(<Counter />);

  expect(screen.getByText("Count: 0")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Increment" }));

  expect(screen.getByText("Count: 1")).toBeInTheDocument();
});

// --- Form submission ---
test("submits form with user input", async () => {
  const user = userEvent.setup();
  const onSubmit = vi.fn();
  render(<LoginForm onSubmit={onSubmit} />);

  await user.type(screen.getByLabelText("Email"), "alice@test.com");
  await user.type(screen.getByLabelText("Password"), "password123");
  await user.click(screen.getByRole("button", { name: "Sign in" }));

  expect(onSubmit).toHaveBeenCalledWith({
    email: "alice@test.com",
    password: "password123",
  });
});

// --- Async content ---
test("loads and displays data", async () => {
  render(<UserList />);

  // Wait for loading to finish
  await waitFor(() => {
    expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
  });

  expect(screen.getByText("Alice")).toBeInTheDocument();
  expect(screen.getByText("Bob")).toBeInTheDocument();
});

// --- Error states ---
test("displays error message", async () => {
  server.use(
    http.get("/api/users", () => HttpResponse.json({ error: "Failed" }, { status: 500 }))
  );

  render(<UserList />);

  await waitFor(() => {
    expect(screen.getByRole("alert")).toHaveTextContent(/error/i);
  });
});

// --- Custom render with providers ---
function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return {
    ...render(
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>{ui}</ThemeProvider>
      </QueryClientProvider>
    ),
  };
}

test("renders with providers", () => {
  renderWithProviders(<Dashboard />);
  expect(screen.getByText("Dashboard")).toBeInTheDocument();
});

// --- Querying by role (preferred for accessibility) ---
test("accessible queries", () => {
  render(<Form />);

  screen.getByRole("button", { name: "Submit" });
  screen.getByRole("textbox", { name: "Email" });
  screen.getByRole("heading", { level: 2 });
  screen.getByLabelText("Password");
});
```

## Common Mistakes

```typescript
// WRONG: Testing implementation details
test("calls setState", () => {
  render(<Counter />);
  expect(component.state.count).toBe(0);  // Don't test state!
});

// CORRECT: Test what the user sees
test("shows count", () => {
  render(<Counter />);
  expect(screen.getByText("Count: 0")).toBeInTheDocument();
});

// WRONG: Using getBy when element may not exist
expect(screen.getByText("No results")).toBeInTheDocument();  // Throws if not found

// CORRECT: Use queryBy for negative assertions
expect(screen.queryByText("No results")).not.toBeInTheDocument();

// WRONG: Not wrapping async tests in waitFor
render(<AsyncComponent />);
expect(screen.getByText("Loaded")).toBeInTheDocument();  // May not be rendered yet

// CORRECT: Use waitFor for async content
await waitFor(() => {
  expect(screen.getByText("Loaded")).toBeInTheDocument();
});

// WRONG: Using container.querySelector
const { container } = render(<Component />);
container.querySelector(".my-class");  // Tests CSS classes, not behavior

// CORRECT: Use screen queries
screen.getByRole("button", { name: "Submit" });

// WRONG: Not using userEvent.setup()
fireEvent.click(button);  // Low-level, doesn't simulate real user behavior

// CORRECT: Use userEvent for realistic interactions
const user = userEvent.setup();
await user.click(button);
```

## Gotchas
- `getBy` throws if not found; `queryBy` returns null; `findBy` waits (async)
- `screen` is the preferred way to query — no need to destructure from `render()`
- `userEvent.setup()` before interactions — more realistic than `fireEvent`
- Use `getByRole` for accessible queries (button, textbox, heading)
- `waitFor` retries until the assertion passes or times out
- `getByText` matches visible text; `getByDisplayText` matches input values
- Custom `renderWithProviders` wrapper keeps tests DRY
- `@testing-library/jest-dom` adds matchers like `toBeInTheDocument()`, `toHaveTextContent()`

## Related
- typescript/testing/msw-mocking.md
- typescript/testing/playwright-e2e.md
- typescript/web/react/hooks.md
