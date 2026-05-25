---
id: "typescript-web-react-error-boundaries"
title: "React Error Boundaries"
language: "typescript"
category: "web"
subcategory: "frontend"
tags: ["react", "error", "boundary", "fallback", "suspense", "catch"]
version: "5.0+"
retrieval_hint: "React error boundary fallback componentDidCatch Suspense error handling"
last_verified: "2026-05-24"
confidence: "high"
---

# React Error Boundaries

## When to Use
- Catching rendering errors in component trees to prevent full-page crashes
- Showing fallback UI instead of blank screens
- Isolating errors to specific sections (sidebar, widget, main content)
- Integration with error reporting (Sentry, LogRocket)

## Standard Pattern

```tsx
import { Component, type ReactNode, type ErrorInfo } from "react";

// --- Error Boundary Component (class-based — required for lifecycle) ---
interface ErrorBoundaryProps {
  children: ReactNode;
  fallback: ReactNode;
  onError?: (error: Error, info: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info.componentStack);
    this.props.onError?.(error, info);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

// --- Usage: wrap components that may fail ---
function App() {
  return (
    <div>
      <Header />
      <ErrorBoundary fallback={<p>Something went wrong with the dashboard.</p>}>
        <Dashboard />
      </ErrorBoundary>
      <Sidebar />
    </div>
  );
}

// --- Reusable fallback component ---
function ErrorFallback({ error, resetError }: { error: Error; resetError: () => void }) {
  return (
    <div role="alert" className="error-fallback">
      <h2>Something went wrong</h2>
      <pre>{error.message}</pre>
      <button onClick={resetError}>Try again</button>
    </div>
  );
}

// --- With reset capability ---
class ResettableErrorBoundary extends Component<
  { children: ReactNode; fallback: (error: Error, reset: () => void) => ReactNode },
  { hasError: boolean; error: Error | null }
> {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  reset = () => this.setState({ hasError: false, error: null });

  render() {
    if (this.state.hasError && this.state.error) {
      return this.props.fallback(this.state.error, this.reset);
    }
    return this.props.children;
  }
}

// --- With Suspense integration ---
function App() {
  return (
    <ErrorBoundary fallback={<ErrorFallback error={new Error("Crash")} resetError={() => {}} />}>
      <Suspense fallback={<Loading />}>
        <LazyDashboard />
      </Suspense>
    </ErrorBoundary>
  );
}
```

## Common Mistakes

```tsx
// WRONG: Error boundary catches too much
<ErrorBoundary fallback={<ErrorPage />}>
  <EntireApp />  // One error crashes everything
</ErrorBoundary>

// CORRECT: Granular boundaries around risky sections
<div>
  <ErrorBoundary fallback={<SidebarError />}>
    <Sidebar />
  </ErrorBoundary>
  <ErrorBoundary fallback={<ContentError />}>
    <MainContent />
  </ErrorBoundary>
</div>

// WRONG: Not handling async errors (error boundaries DON'T catch them)
async function loadData() {
  throw new Error("API failed");  // NOT caught by error boundary!
}

// CORRECT: Convert async errors to state
function Dashboard() {
  const [error, setError] = useState<Error | null>(null);
  if (error) throw error;  // Now caught by boundary
  // ...
}

// WRONG: Error boundary as functional component
function ErrorBoundary({ children }) {  // Can't use getDerivedStateFromError
  return children;
}

// CORRECT: Must be a class component (React limitation)
class ErrorBoundary extends Component { ... }
```

## Gotchas
- Error boundaries MUST be class components — no functional equivalent exists yet
- They catch errors during rendering, lifecycle methods, and constructors
- They do NOT catch errors in event handlers, async code, or server-side rendering
- Wrap async errors in state and throw during render to trigger the boundary
- `componentDidCatch` is for logging; `getDerivedStateFromError` is for updating state
- Multiple boundaries can be nested — inner boundaries catch first
- Use `react-error-boundary` library for a simpler API with functional components
- Error boundaries reset when you change their `key` prop

## Related
- typescript/testing/playwright-e2e.md
- typescript/web/nextjs/app-router.md
- typescript/web/react/hooks.md
