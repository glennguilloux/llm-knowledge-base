---
id: "typescript-web-react-performance"
title: "React Performance: useMemo, useCallback, React.memo"
language: "typescript"
category: "web"
subcategory: "frontend"
tags: ["react", "performance", "memo", "usememo", "usecallback", "re-render"]
version: "5.0+"
retrieval_hint: "React performance useMemo useCallback React.memo re-render optimization"
last_verified: "2026-05-22"
confidence: "high"
---

# React Performance: useMemo, useCallback, React.memo

## When to Use
- Expensive computations that shouldn't run every render (`useMemo`)
- Stable function references for child components that check reference equality (`useCallback`)
- Preventing child re-renders when props haven't changed (`React.memo`)
- Lists with many items where parent state changes frequently

## Standard Pattern

```tsx
import { memo, useMemo, useCallback, useState } from "react";

// --- React.memo: skip re-render if props unchanged ---
interface UserCardProps {
  user: User;
  onSelect: (id: string) => void;
}

const UserCard = memo(function UserCard({ user, onSelect }: UserCardProps) {
  console.log(`Rendering UserCard: ${user.name}`);
  return (
    <div onClick={() => onSelect(user.id)}>
      <h3>{user.name}</h3>
      <p>{user.email}</p>
    </div>
  );
});

// --- useMemo: memoize expensive computation ---
function UserList({ users, filter }: { users: User[]; filter: string }) {
  // Only recomputes when users or filter changes
  const filteredUsers = useMemo(
    () => users.filter((u) => u.name.toLowerCase().includes(filter.toLowerCase())),
    [users, filter]
  );

  // Expensive sort — only when filtered list changes
  const sortedUsers = useMemo(
    () => [...filteredUsers].sort((a, b) => a.name.localeCompare(b.name)),
    [filteredUsers]
  );

  return (
    <div>
      {sortedUsers.map((user) => (
        <UserCard key={user.id} user={user} onSelect={handleSelect} />
      ))}
    </div>
  );
}

// --- useCallback: stable function references ---
function UserPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [selected, setSelected] = useState<string | null>(null);

  // Stable reference — UserCard won't re-render just because UserPage re-rendered
  const handleSelect = useCallback((id: string) => {
    setSelected(id);
  }, []);

  // Stable reference for the list
  const handleDelete = useCallback((id: string) => {
    setUsers((prev) => prev.filter((u) => u.id !== id));
  }, []);

  return (
    <div>
      <UserList users={users} onSelect={handleSelect} onDelete={handleDelete} />
      {selected && <UserDetail id={selected} />}
    </div>
  );
}

// --- Derived state with useMemo ---
function Dashboard({ data }: { data: RawData }) {
  const stats = useMemo(() => ({
    total: data.items.length,
    active: data.items.filter((i) => i.isActive).length,
    revenue: data.items.reduce((sum, i) => sum + i.price, 0),
  }), [data.items]);

  return <StatsPanel stats={stats} />;
}
```

## Common Mistakes

```tsx
// WRONG: Wrapping everything in useMemo (premature optimization)
const fullName = useMemo(() => `${first} ${last}`, [first, last]);  // Trivial computation

// CORRECT: Only memoize expensive computations
const sorted = useMemo(() => items.toSorted(comparator), [items]);  // O(n log n)

// WRONG: useCallback without memoizing the child (still re-renders)
const handleClick = useCallback(() => doSomething(id), [id]);
<ExpensiveChild onClick={handleClick} />  // ExpensiveChild is NOT memoized — still re-renders!

// CORRECT: Memoize the child too
const ExpensiveChild = memo(function ExpensiveChild({ onClick }) { ... });
const handleClick = useCallback(() => doSomething(id), [id]);
<ExpensiveChild onClick={handleClick} />  // Now it skips re-render

// WRONG: Missing dependency in useMemo/useCallback
const filtered = useMemo(() => items.filter((i) => i.name.includes(search)), []);
// search is stale — always uses initial value!

// CORRECT: Include all dependencies
const filtered = useMemo(() => items.filter((i) => i.name.includes(search)), [items, search]);

// WRONG: New object/array as prop (breaks memo)
<UserCard user={{ ...userData, extra: true }} />  // New object every render

// CORRECT: Memoize the object
const userWithExtra = useMemo(() => ({ ...userData, extra: true }), [userData]);
<UserCard user={userWithExtra} />
```

## Gotchas
- `React.memo` does shallow comparison — new objects/arrays as props bypass it
- `useCallback(fn, deps)` is equivalent to `useMemo(() => fn, deps)`
- Don't memoize everything — there's overhead in memoization itself
- Profile with React DevTools before optimizing — re-renders aren't always the bottleneck
- `useMemo` doesn't guarantee the value is kept — React may discard it under memory pressure
- Use the React Compiler (React 19+) for automatic memoization — manual memo may be unnecessary
- `memo` wraps the component — the comparison happens on props, not internal state
- `useCallback` with `[]` deps creates a function that never changes — be careful with closures

## Related
- typescript/web/react/hooks.md
- typescript/web/react/context.md
- typescript/web/react/state.md
