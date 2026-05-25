---
id: "typescript-web-nextjs-app-router"
title: "Next.js App Router"
language: "typescript"
category: "web"
subcategory: "framework"
tags: ["nextjs", "app-router", "server-components", "layout", "routing"]
version: "14+"
retrieval_hint: "Next.js App Router server components layout routing"
last_verified: "2026-05-24"
confidence: "high"
---

# Next.js App Router

## When to Use
- Building React applications with server-side rendering
- File-based routing with layouts
- Server and client components
- Data fetching patterns

## Standard Pattern

```typescript
// app/layout.tsx - Root layout (required)
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

// app/page.tsx - Home page (server component by default)
export default async function HomePage() {
  const data = await fetch('https://api.example.com/data', {
    cache: 'no-store',  // or 'force-cache'
  });
  const items = await data.json();

  return (
    <main>
      <h1>Home</h1>
      <ItemList items={items} />
    </main>
  );
}

// app/items/[id]/page.tsx - Dynamic route
interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function ItemPage({ params }: PageProps) {
  const { id } = await params;
  const item = await fetchItem(id);

  if (!item) {
    notFound();
  }

  return <ItemDetails item={item} />;
}

// app/items/[id]/loading.tsx - Loading UI
export default function Loading() {
  return <div>Loading...</div>;
}

// app/items/[id]/error.tsx - Error boundary
'use client';

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={reset}>Try again</button>
    </div>
  );
}

// Client component
'use client';

import { useState } from 'react';

export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>;
}
```

## Common Mistakes

```typescript
// WRONG: Using useState in server component
export default function Page() {
  const [data, setData] = useState([]);  // Error: server component!
  return <div>{data}</div>;
}

// CORRECT: Add 'use client' for client components
'use client';
export default function Page() {
  const [data, setData] = useState([]);
  return <div>{data}</div>;
}

// WRONG: Not awaiting params
export default function Page({ params }: { params: { id: string } }) {
  const id = params.id;  // params is a Promise in Next.js 15+!
}

// CORRECT: Await params
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
}

// WRONG: 'use client' on a layout that wraps server components
'use client';
export default function Layout({ children }: { children: React.ReactNode }) {
  return <div><nav /><main>{children}</main></div>;  // All children become client!
}

// CORRECT: Keep layout as server component, extract interactive parts
export default function Layout({ children }: { children: React.ReactNode }) {
  return <div><Nav /><main>{children}</main></div>;
}
'use client';
function Nav() {
  const [open, setOpen] = useState(false);
  return <nav>{/* interactive logic here */}</nav>;
}
```

## Gotchas
- Server components are the default; add `'use client'` for client components
- `params` is a Promise in Next.js 15+ — must be awaited
- Use `cache: 'no-store'` for dynamic data, `cache: 'force-cache'` for static
- `loading.tsx` shows loading UI while page data fetches
- `error.tsx` catches errors (must be client component)
- `notFound()` triggers the nearest `not-found.tsx`
- Layouts persist across navigations; pages re-render

## Related
- typescript/web/nextjs/server-actions.md
- typescript/web/nextjs/data-fetching.md
- typescript/web/nextjs/middleware.md
