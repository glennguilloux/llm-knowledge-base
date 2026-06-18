---
id: "anti-patterns-typescript-useeffect-cleanup"
title: "React/TypeScript Anti-Pattern: useEffect Cleanup"
language: "typescript"
category: "anti-patterns"
tags: ["antipatterns", "typescript", "react", "hooks", "useeffect", "cleanup", "memory-leak"]
version: "n/a"
retrieval_hint: "React useEffect cleanup memory leak stale closure subscription abort controller timer interval unmounted component"
last_verified: "2026-05-24"
confidence: "high"
---

# React/TypeScript Anti-Pattern: useEffect Cleanup

## When to Use
- Reviewing React components with subscriptions, timers, or async operations
- Training LLMs to properly clean up side effects in useEffect
- Debugging "Can't perform a React state update on an unmounted component" warnings
- Building robust React components that don't leak resources

## Standard Pattern

```typescript
import { useEffect, useState, useRef, useCallback } from "react";

// ---------------------------------------------------------------------------
// WRONG: Missing cleanup for subscriptions
// ---------------------------------------------------------------------------

// WRONG: WebSocket — no cleanup, connection stays open forever
function LivePrices() {
  const [price, setPrice] = useState(0);

  useEffect(() => {
    const ws = new WebSocket("wss://prices.example.com");
    ws.onmessage = (event) => {
      setPrice(JSON.parse(event.data).price);
    };
    // ❌ No cleanup — WebSocket stays open on unmount
  }, []);

  return <div>Price: {price}</div>;
}

// CORRECT: Close WebSocket on cleanup
function LivePrices() {
  const [price, setPrice] = useState(0);

  useEffect(() => {
    const ws = new WebSocket("wss://prices.example.com");
    ws.onmessage = (event) => {
      setPrice(JSON.parse(event.data).price);
    };

    return () => {
      ws.close(); // ✅ Proper cleanup
    };
  }, []);

  return <div>Price: {price}</div>;
}

// ---------------------------------------------------------------------------
// WRONG: Not clearing timers (setInterval / setTimeout)
// ---------------------------------------------------------------------------

// WRONG: setInterval with no cleanup — runs forever, state updates on unmounted component
function PollingStatus() {
  const [status, setStatus] = useState("idle");

  useEffect(() => {
    setInterval(async () => {
      const res = await fetch("/api/status");
      const data = await res.json();
      setStatus(data.status);
      // ❌ After unmount: "Can't perform a React state update on unmounted component"
    }, 5000);
  }, []);

  return <div>Status: {status}</div>;
}

// CORRECT: Clear interval on cleanup
function PollingStatus() {
  const [status, setStatus] = useState("idle");

  useEffect(() => {
    const intervalId = setInterval(async () => {
      try {
        const res = await fetch("/api/status");
        const data = await res.json();
        setStatus(data.status);
      } catch {
        // Handle error
      }
    }, 5000);

    return () => clearInterval(intervalId); // ✅ Cleanup
  }, []);

  return <div>Status: {status}</div>;
}

// ---------------------------------------------------------------------------
// WRONG: AbortController not used for fetch
// ---------------------------------------------------------------------------

// WRONG: Fetch continues after unmount (wasted bandwidth, state update on unmounted)
function SearchResults({ query }: { query: string }) {
  const [results, setResults] = useState<string[]>([]);

  useEffect(() => {
    fetch(`/api/search?q=${query}`)
      .then((res) => res.json())
      .then((data) => setResults(data.results));
    // ❌ If component unmounts or query changes, old fetch still resolves
  }, [query]);

  return <ul>{results.map((r) => <li key={r}>{r}</li>)}</ul>;
}

// CORRECT: Abort previous request on cleanup
function SearchResults({ query }: { query: string }) {
  const [results, setResults] = useState<string[]>([]);

  useEffect(() => {
    const abortController = new AbortController();

    fetch(`/api/search?q=${query}`, { signal: abortController.signal })
      .then((res) => res.json())
      .then((data) => {
        if (!abortController.signal.aborted) {
          setResults(data.results);
        }
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          console.error("Search failed:", err);
        }
      });

    return () => abortController.abort(); // ✅ Abort on cleanup
  }, [query]);

  return <ul>{results.map((r) => <li key={r}>{r}</li>)}</ul>;
}

// ---------------------------------------------------------------------------
// WRONG: Stale closure in useEffect
// ---------------------------------------------------------------------------

// WRONG: Closure captures old state values
function Counter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const intervalId = setInterval(() => {
      console.log(count);   // Always 0 — stale closure!
      setCount(count + 1);  // Always set to 1
    }, 1000);

    return () => clearInterval(intervalId);
  }, []);  // Empty deps — count is captured once

  return <div>{count}</div>;
}

// CORRECT: Use functional update or include deps
function Counter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const intervalId = setInterval(() => {
      setCount((prev) => prev + 1);  // ✅ Functional update — no stale closure
    }, 1000);

    return () => clearInterval(intervalId);
  }, []);

  return <div>{count}</div>;
}

// ---------------------------------------------------------------------------
// WRONG: Missing dependencies in deps array
// ---------------------------------------------------------------------------

// WRONG: useEffect with missing deps — sneaky bugs
function UserProfile({ userId }: { userId: number }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then((res) => res.json())
      .then(setUser);
    // ⚠️ React Hook useEffect has a missing dependency: 'userId'
  }, []);  // ❌ userId missing — effect doesn't update when userId changes

  return <div>{user?.name}</div>;
}

// CORRECT: Include all reactive values in deps
function UserProfile({ userId }: { userId: number }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then((res) => res.json())
      .then(setUser);
  }, [userId]);  // ✅ Deps include userId

  return <div>{user?.name}</div>;
}

// ---------------------------------------------------------------------------
// WRONG: async function directly in useEffect
// ---------------------------------------------------------------------------

// WRONG: useEffect callback can't be async directly
useEffect(async () => {
  // ❌ Returns a Promise, not a cleanup function or undefined
  // React calls the cleanup function, which is now a resolved promise — no-op
  const data = await fetch("/api/data");
  setData(await data.json());
}, []);

// CORRECT: Define async function inside, call it
useEffect(() => {
  let cancelled = false;

  async function loadData() {
    const res = await fetch("/api/data");
    const data = await res.json();
    if (!cancelled) {
      setData(data);
    }
  }

  loadData();

  return () => {
    cancelled = true;  // ✅ Prevent state update on unmount
  };
}, []);
```

## Common Mistakes
The most common error is forgetting cleanup entirely — subscriptions, timers, and fetch requests continue running after the component unmounts, causing wasted resources and "Can't perform a React state update on an unmounted component" warnings. Second: stale closures, where the effect callback captures an old version of state or props because the dependency array is incorrect. Third: directly passing `async` functions to `useEffect` — the returned Promise is mistaken for a cleanup function.

## Gotchas
- `useEffect` cleanup runs on every re-render (before the new effect) AND on unmount — not just unmount
- A missing cleanup for `setInterval` causes the interval to run indefinitely, even after the component is unmounted
- `AbortController.abort()` throws `AbortError` in the fetch promise — always check `err.name !== "AbortError"` in catch
- `fetch` doesn't auto-abort on unmount — you MUST manually abort or use a boolean flag (but AbortController is cleaner)
- React's Strict Mode (dev only) runs effects twice — this can expose missing cleanup bugs that don't appear in production
- Stale closures happen when the effect doesn't re-run after a dependency changes — always list all reactive values in the deps array
- The `exhaustive-deps` ESLint rule catches most missing dependency bugs — enable `react-hooks/exhaustive-deps`
- `useRef` values are NOT reactive — putting them in deps won't trigger re-runs; use them for mutable values that shouldn't cause re-renders
- Function references in deps cause infinite re-renders if the function is recreated every render — use `useCallback`
- `useEffect` with empty deps `[]` runs only once (mount) — the cleanup runs only on unmount
- Multiple effects are better than one — each effect should handle a single concern with its own cleanup
- The `return () => {}` pattern also works for cancelling event listeners: `window.removeEventListener`

## Related
- anti-patterns/typescript-antipatterns.md
- anti-patterns/react-antipatterns.md
