---
id: "typescript-web-react-hooks"
title: "React Custom Hooks"
language: "typescript"
category: "web"
subcategory: "react"
tags: ["react", "hooks", "custom-hooks", "use-state", "use-effect"]
version: "18+"
retrieval_hint: "React custom hooks useState useEffect useReducer"
last_verified: "2026-05-22"
confidence: "high"
---

# React Custom Hooks

## When to Use
- Reusing stateful logic across components
- Abstracting complex side effects
- Building reusable data-fetching patterns
- Encapsulating form logic

## Standard Pattern

```typescript
import { useState, useEffect, useCallback, useRef } from 'react';

// useLocalStorage - persist state to localStorage
function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T | ((prev: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback((value: T | ((prev: T) => T)) => {
    setStoredValue(prev => {
      const nextValue = value instanceof Function ? value(prev) : value;
      window.localStorage.setItem(key, JSON.stringify(nextValue));
      return nextValue;
    });
  }, [key]);

  return [storedValue, setValue];
}

// useFetch - data fetching with loading and error states
function useFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchData() {
      try {
        setLoading(true);
        const response = await fetch(url, { signal: controller.signal });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        setData(data);
      } catch (err) {
        if (err instanceof Error && err.name !== 'AbortError') {
          setError(err);
        }
      } finally {
        setLoading(false);
      }
    }

    fetchData();
    return () => controller.abort();
  }, [url]);

  return { data, loading, error };
}

// useDebounce - debounce a value
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// usePrevious - track previous value
function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>();
  useEffect(() => {
    ref.current = value;
  }, [value]);
  return ref.current;
}

// Usage
function SearchComponent() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 300);
  const { data, loading, error } = useFetch<Item[]>(
    `/api/search?q=${debouncedQuery}`
  );

  return (
    <div>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      {loading && <p>Loading...</p>}
      {error && <p>Error: {error.message}</p>}
      {data && <ItemList items={data} />}
    </div>
  );
}
```

## Common Mistakes

```typescript
// WRONG: Calling hooks conditionally
function Component({ show }: { show: boolean }) {
  if (show) {
    const [value, setValue] = useState(0);  // Error: hooks must be called unconditionally!
  }
}

// CORRECT: Always call hooks at the top level
function Component({ show }: { show: boolean }) {
  const [value, setValue] = useState(0);
  if (!show) return null;
}

// WRONG: Missing dependency in useEffect
function Component({ id }: { id: string }) {
  useEffect(() => {
    fetchData(id);  // Warning: missing dependency 'id'
  }, []);  // Only runs once!
}

// CORRECT: Include all dependencies
function Component({ id }: { id: string }) {
  useEffect(() => {
    fetchData(id);
  }, [id]);
}
```

## Gotchas
- Hooks must be called at the top level (not in conditions or loops)
- Custom hooks must start with "use"
- `useEffect` cleanup runs before the next effect and on unmount
- `useCallback` memoizes functions; `useMemo` memoizes values
- `useRef` persists across renders without causing re-renders
- Always include all dependencies in `useEffect` dependency array
- Use `AbortController` to cancel fetch requests on cleanup

## Real-World Example

### Data Fetching Hook with Retry, Cache, and Optimistic Updates

```typescript
import { useState, useEffect, useCallback, useRef } from "react";

interface UseFetchOptions<T> {
  retries?: number;
  retryDelay?: number;
  enabled?: boolean;
}

interface UseFetchResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

function useFetch<T>(
  url: string,
  options: UseFetchOptions<T> = {}
): UseFetchResult<T> {
  const { retries = 3, retryDelay = 1000, enabled = true } = options;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const fetchData = useCallback(
    async (attempt = 0) => {
      abortRef.current?.abort();
      abortRef.current = new AbortController();
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(url, { signal: abortRef.current.signal });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const json = await response.json();
        setData(json);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        if (attempt < retries) {
          await new Promise((r) => setTimeout(r, retryDelay * (attempt + 1)));
          return fetchData(attempt + 1);
        }
        setError(err instanceof Error ? err : new Error(String(err)));
      } finally {
        setLoading(false);
      }
    },
    [url, retries, retryDelay]
  );

  useEffect(() => {
    if (enabled) fetchData();
    return () => abortRef.current?.abort();
  }, [enabled, fetchData]);

  return { data, loading, error, refetch: () => fetchData() };
}

// Usage
function UserList() {
  const { data, loading, error, refetch } = useFetch<User[]>("/api/users", {
    retries: 2,
  });
  if (loading) return <Spinner />;
  if (error) return <ErrorBanner error={error} onRetry={refetch} />;
  return <ul>{data?.map((u) => <li key={u.id}>{u.name}</li>)}</ul>;
}
```

## Related
- typescript/web/react/state.md
- typescript/web/nextjs/app-router.md
