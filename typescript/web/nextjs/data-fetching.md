---
id: "typescript-web-nextjs-data-fetching"
title: "Next.js Data Fetching"
language: "typescript"
category: "web"
subcategory: "data-fetching"
tags: ["nextjs", "data-fetching", "server-components", "cache", "revalidation"]
version: "14+"
retrieval_hint: "Next.js data fetching server components cache revalidation"
last_verified: "2026-05-24"
confidence: "high"
---

# Next.js Data Fetching

## When to Use
- Fetching data in server components
- Caching strategies
- Revalidation patterns
- Parallel data fetching

## Standard Pattern

```typescript
// Server component data fetching
export default async function UsersPage() {
  const users = await fetch('https://api.example.com/users', {
    cache: 'no-store',  // Dynamic: fresh on every request
    // cache: 'force-cache',  // Static: cached until revalidated
    // next: { revalidate: 3600 },  // ISR: revalidate every hour
  }).then(res => res.json());

  return <UserList users={users} />;
}

// With fetch wrapper
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`https://api.example.com${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

// Parallel data fetching
export default async function DashboardPage() {
  const [users, orders, analytics] = await Promise.all([
    fetchAPI<User[]>('/users'),
    fetchAPI<Order[]>('/orders'),
    fetchAPI<Analytics>('/analytics'),
  ]);

  return (
    <div>
      <UsersWidget data={users} />
      <OrdersWidget data={orders} />
      <AnalyticsWidget data={analytics} />
    </div>
  );
}

// With revalidation
async function getItems() {
  const res = await fetch('https://api.example.com/items', {
    next: { revalidate: 3600, tags: ['items'] },
  });
  return res.json();
}

// On-demand revalidation
'use server';
import { revalidateTag } from 'next/cache';

export async function refreshItems() {
  revalidateTag('items');
}

// Static generation with dynamic params
export async function generateStaticParams() {
  const items = await fetchAPI<Item[]>('/items');
  return items.map(item => ({ id: item.id }));
}
```

## Common Mistakes

```typescript
// WRONG: Fetching in useEffect (client component)
'use client';
export default function Page() {
  const [data, setData] = useState([]);
  useEffect(() => {
    fetch('/api/data').then(res => res.json()).then(setData);
  }, []);  // Extra client-server round trip!
}

// CORRECT: Fetch in server component
export default async function Page() {
  const data = await fetchAPI('/api/data');
  return <DataDisplay data={data} />;
}

// WRONG: Not caching static data
export default async function Page() {
  const data = await fetch('https://api.example.com/static-data');  // Fetched every request!
}

// CORRECT: Cache static data
export default async function Page() {
  const data = await fetch('https://api.example.com/static-data', {
    cache: 'force-cache',
  });
}

// WRONG: Same fetch URL and options but expecting different data
export default async function PageA() {
  const data = await fetch('https://api.example.com/items');  // Cached!
}
export default async function PageB() {
  const data = await fetch('https://api.example.com/items');  // Same cache hit!
}

// CORRECT: Use distinct cache keys or revalidation
export default async function PageA() {
  const data = await fetch('https://api.example.com/items', {
    next: { tags: ['items-a'] },
  });
}
export default async function PageB() {
  const data = await fetch('https://api.example.com/items', {
    next: { tags: ['items-b'] },
  });
}
```

## Gotchas
- `cache: 'no-store'` = dynamic (no cache)
- `cache: 'force-cache'` = static (cached until revalidated)
- `next: { revalidate: N }` = ISR (revalidate every N seconds)
- `next: { tags: ['tag'] }` = on-demand revalidation with `revalidateTag()`
- `Promise.all()` for parallel fetching
- `generateStaticParams()` for static generation of dynamic routes
- Errors in data fetching trigger `error.tsx`

## Related
- typescript/web/nextjs/app-router.md
- typescript/web/nextjs/server-actions.md
