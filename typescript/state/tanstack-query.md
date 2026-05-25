---
id: "typescript-state-tanstack-query"
title: "TanStack Query (React Query) Data Fetching"
language: "typescript"
category: "web"
subcategory: "data-fetching"
tags: ["react-query", "tanstack", "data-fetching", "cache", "stale", "mutation"]
version: "5.0+"
retrieval_hint: "TanStack Query React Query data fetching cache stale mutation useQuery useMutation"
last_verified: "2026-05-24"
confidence: "high"
---

# TanStack Query (React Query) Data Fetching

## When to Use
- Server state management (data from APIs that can become stale)
- Caching, deduplicating, and refetching API requests
- Optimistic updates for mutations (instant UI feedback)
- Pagination, infinite scroll, and background data refetching

## Standard Pattern

```typescript
import { useQuery, useMutation, useQueryClient, QueryClient, QueryClientProvider } from "@tanstack/react-query";

// --- Setup ---
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,    // 5 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <UserList />
    </QueryClientProvider>
  );
}

// --- Fetching data ---
interface User {
  id: number;
  name: string;
  email: string;
}

async function fetchUsers(): Promise<User[]> {
  const res = await fetch("/api/users");
  if (!res.ok) throw new Error("Failed to fetch users");
  return res.json();
}

function UserList() {
  const { data: users, isLoading, error, refetch } = useQuery({
    queryKey: ["users"],
    queryFn: fetchUsers,
  });

  if (isLoading) return <Loading />;
  if (error) return <Error error={error} onRetry={refetch} />;

  return (
    <ul>
      {users?.map((user) => (
        <UserCard key={user.id} user={user} />
      ))}
    </ul>
  );
}

// --- Dependent queries ---
function UserProfile({ userId }: { userId: number }) {
  const { data: user } = useQuery({
    queryKey: ["user", userId],
    queryFn: () => fetchUser(userId),
  });

  const { data: posts } = useQuery({
    queryKey: ["posts", userId],
    queryFn: () => fetchUserPosts(userId),
    enabled: !!user,  // Only fetch after user loads
  });
}

// --- Mutations with cache invalidation ---
function CreateUserForm() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (newUser: { name: string; email: string }) =>
      fetch("/api/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newUser),
      }).then((res) => res.json()),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      mutation.mutate({ name: "Alice", email: "alice@test.com" });
    }}>
      {mutation.isPending && <span>Creating...</span>}
      {mutation.isError && <span>Error: {mutation.error.message}</span>}
      <button type="submit" disabled={mutation.isPending}>Create User</button>
    </form>
  );
}

// --- Optimistic updates ---
function TodoItem({ todo }: { todo: Todo }) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (updated: Todo) =>
      fetch(`/api/todos/${updated.id}`, { method: "PUT", body: JSON.stringify(updated) }),

    onMutate: async (updated) => {
      await queryClient.cancelQueries({ queryKey: ["todos"] });
      const previous = queryClient.getQueryData(["todos"]);
      queryClient.setQueryData(["todos"], (old: Todo[]) =>
        old.map((t) => (t.id === updated.id ? updated : t))
      );
      return { previous };
    },

    onError: (_err, _updated, context) => {
      queryClient.setQueryData(["todos"], context?.previous);
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
  });
}
```

## Common Mistakes

```typescript
// WRONG: Fetching in useEffect with useState
const [users, setUsers] = useState([]);
const [loading, setLoading] = useState(true);
useEffect(() => {
  fetch("/api/users").then(r => r.json()).then(setUsers).finally(() => setLoading(false));
}, []);  // No caching, no deduplication, no background refetch

// CORRECT: Use useQuery
const { data: users, isLoading } = useQuery({ queryKey: ["users"], queryFn: fetchUsers });

// WRONG: Query key doesn't include variables
useQuery({ queryKey: ["users"], queryFn: () => fetchUser(userId) });
// Different userIds share the same cache entry!

// CORRECT: Include variables in query key
useQuery({ queryKey: ["user", userId], queryFn: () => fetchUser(userId) });

// WRONG: Not invalidating cache after mutation
mutation.mutate(newUser);  // List shows stale data until refetch

// CORRECT: Invalidate related queries
onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] });

// WRONG: Calling useQuery conditionally
if (userId) {
  const { data } = useQuery(...);  // React hooks rule violation!
}

// CORRECT: Use enabled option
const { data } = useQuery({ queryKey: ["user", userId], queryFn: ..., enabled: !!userId });
```

## Gotchas
- `queryKey` is the cache key — include all variables that affect the query
- `staleTime` controls how long data is considered fresh (no refetch)
- `enabled: false` disables automatic fetching — useful for dependent queries
- `queryClient.invalidateQueries()` triggers background refetch for matching keys
- Optimistic updates: `onMutate` → `onError` (rollback) → `onSettled` (refetch)
- `useMutation` doesn't fetch data — it's for POST/PUT/DELETE operations
- Use `queryClient.setQueryData()` for instant cache updates without refetching
- React Query DevTools (`@tanstack/react-query-devtools`) for debugging cache state

## Related
- typescript/state/zustand-patterns.md
- typescript/web/react/hooks.md
- typescript/web/nextjs/data-fetching.md
