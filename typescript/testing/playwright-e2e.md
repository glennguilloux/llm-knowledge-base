---
id: "typescript-testing-playwright-e2e"
title: "Playwright E2E Testing"
language: "typescript"
category: "testing"
subcategory: "e2e"
tags: ["playwright", "e2e", "testing", "browser", "automation", "selectors"]
version: "5.0+"
retrieval_hint: "Playwright E2E testing browser automation selectors page test expect"
last_verified: "2026-05-24"
confidence: "high"
---

# Playwright E2E Testing

## When to Use
- End-to-end testing of critical user flows (login, checkout, signup)
- Cross-browser testing (Chromium, Firefox, WebKit)
- Visual regression testing with screenshots
- Testing complex interactions (drag-and-drop, file upload, WebSocket)

## Standard Pattern

```typescript
import { test, expect, Page } from "@playwright/test";

// --- Basic test ---
test("homepage loads correctly", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/My App/);
  await expect(page.locator("h1")).toContainText("Welcome");
});

// --- Login flow ---
test("user can log in", async ({ page }) => {
  await page.goto("/login");
  await page.fill('[data-testid="email-input"]', "alice@test.com");
  await page.fill('[data-testid="password-input"]', "password123");
  await page.click('[data-testid="login-button"]');

  await expect(page).toHaveURL("/dashboard");
  await expect(page.locator('[data-testid="user-menu"]')).toContainText("Alice");
});

// --- Form submission ---
test("create a new post", async ({ page }) => {
  await page.goto("/posts/new");
  await page.fill('input[name="title"]', "My New Post");
  await page.fill('textarea[name="content"]', "Post content here");
  await page.click('button[type="submit"]');

  await expect(page.locator(".toast")).toContainText("Post created");
  await expect(page.locator("h1")).toContainText("My New Post");
});

// --- API interception ---
test("handles API error gracefully", async ({ page }) => {
  await page.route("**/api/users", (route) =>
    route.fulfill({ status: 500, body: JSON.stringify({ error: "Server error" }) })
  );

  await page.goto("/users");
  await expect(page.locator('[data-testid="error-message"]')).toContainText("Something went wrong");
});

// --- Network request verification ---
test("makes correct API call", async ({ page }) => {
  const requestPromise = page.waitForRequest("**/api/users");
  await page.goto("/users");
  const request = await requestPromise;
  expect(request.method()).toBe("GET");
});

// --- Multi-tab testing ---
test("opens in new tab", async ({ page, context }) => {
  const newPagePromise = context.waitForEvent("page");
  await page.click('a[target="_blank"]');
  const newPage = await newPagePromise;
  await expect(newPage).toHaveURL(/\/detail/);
});

// --- File upload ---
test("uploads a file", async ({ page }) => {
  await page.goto("/upload");
  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles("test-files/document.pdf");
  await expect(page.locator(".upload-success")).toBeVisible();
});

// --- Screenshot comparison ---
test("visual regression", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page).toHaveScreenshot("dashboard.png", {
    maxDiffPixelRatio: 0.01,
  });
});

// --- Page Object Model ---
class LoginPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto("/login");
  }

  async login(email: string, password: string) {
    await this.page.fill('[data-testid="email"]', email);
    await this.page.fill('[data-testid="password"]', password);
    await this.page.click('[data-testid="submit"]');
  }

  async getError() {
    return this.page.locator('[data-testid="error"]').textContent();
  }
}

test("login with POM", async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login("alice@test.com", "wrong");
  expect(await loginPage.getError()).toBe("Invalid credentials");
});
```

## Common Mistakes

```typescript
// WRONG: Using brittle selectors
await page.click("div > span:nth-child(3)");  // Breaks on any DOM change

// CORRECT: Use data-testid or role selectors
await page.click('[data-testid="submit-button"]');
await page.getByRole("button", { name: "Submit" });

// WRONG: Not waiting for elements
await page.click("button");  // May click before button appears

// CORRECT: Wait for element to be visible
await page.waitForSelector("button", { state: "visible" });
await page.click("button");

// WRONG: Hardcoded waits
await page.waitForTimeout(3000);  // Flaky — too short or too long

// CORRECT: Wait for specific conditions
await page.waitForURL("/dashboard");
await expect(page.locator(".loaded")).toBeVisible();

// WRONG: Not using data-testid
await page.locator("button.submit").click();  // CSS class may change

// CORRECT: Use data-testid for test-specific selectors
await page.locator('[data-testid="submit"]').click();
```

## Gotchas
- `data-testid` attributes are the most stable selectors — add them to your components
- Playwright auto-waits for elements to be visible, enabled, and stable before clicking
- `page.route()` intercepts network requests — useful for mocking APIs
- `expect(page).toHaveScreenshot()` creates baseline images on first run
- Use `test.describe()` to group related tests
- `npx playwright test --ui` opens the interactive test runner
- `test.beforeEach()` runs before each test — use for auth setup
- Use `storageState` to persist login across tests (avoid logging in every test)

## Related
- typescript/testing/react-testing-library.md
- typescript/testing/msw-mocking.md
- typescript/web/react/error-boundaries.md
