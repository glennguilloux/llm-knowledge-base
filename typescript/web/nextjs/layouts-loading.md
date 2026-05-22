---
id: "typescript-web-nextjs-layouts-loading"
title: "Next.js Layouts, Loading States, and Error Handling"
language: "typescript"
category: "web"
subcategory: "frontend"
tags: ["nextjs", "layout", "loading", "error", "app-router", "suspense"]
version: "5.0+"
retrieval_hint: "Next.js layout loading error app router Suspense template nested"
last_verified: "2026-05-22"
confidence: "high"
---

# Next.js Layouts, Loading States, and Error Handling

## When to Use
- Persistent UI across routes (nav, sidebar) without re-rendering
- Streaming loading UI with React Suspense
- Per-route error handling with error.tsx
- Shared layouts for sections of the app (dashboard, settings)

## Standard Pattern

```tsx
// --- app/layout.tsx: Root layout (wraps everything) ---
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}

// --- app/dashboard/layout.tsx: Nested layout ---
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex">
      <Sidebar />
      <div className="flex-1">{children}</div>
    </div>
  );
}

// --- app/dashboard/loading.tsx: Loading UI (Suspense fallback) ---
export default function DashboardLoading() {
  return (
    <div className="animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-1/3 mb-4" />
      <div className="h-4 bg-gray-200 rounded w-2/3 mb-2" />
      <div className="h-4 bg-gray-200 rounded w-1/2" />
    </div>
  );
}

// --- app/dashboard/error.tsx: Error boundary ---
"use client";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div role="alert" className="p-4 bg-red-50 border border-red-200 rounded">
      <h2 className="text-red-800 font-bold">Something went wrong</h2>
      <p className="text-red-600">{error.message}</p>
      <button onClick={reset} className="mt-2 px-4 py-2 bg-red-600 text-white rounded">
        Try again
      </button>
    </div>
  );
}

// --- app/dashboard/not-found.tsx: 404 page ---
export default function NotFound() {
  return (
    <div>
      <h2>Page Not Found</h2>
      <p>The page you're looking for doesn't exist.</p>
    </div>
  );
}

// --- Route groups: shared layout without affecting URL ---
// app/(marketing)/layout.tsx — shared layout for /, /about, /pricing
// app/(dashboard)/layout.tsx — shared layout for /dashboard, /settings
// URLs: /about (not /marketing/about)
```

## Common Mistakes

```tsx
// WRONG: Putting client-side state in layout (persists across navigations)
export default function Layout({ children }) {
  const [count, setCount] = useState(0);  // Persists! Count survives navigation
  return <div>{children}</div>;
}

// CORRECT: Use state in pages, not layouts (pages are fresh on each navigation)

// WRONG: Not making error.tsx a client component
// app/dashboard/error.tsx
export default function Error({ error }) {  // Build error!
  return <div>{error.message}</div>;
}

// CORRECT: Add "use client" directive
"use client";
export default function Error({ error, reset }) { ... }

// WRONG: Fetching data in layout (layouts don't await in App Router)
export default async function Layout() {
  const data = await fetchData();  // Blocks ALL nested content
  return <div>{data.title}</div>;
}

// CORRECT: Fetch in pages, or use client-side fetching in layouts
export default function Layout({ children }) {
  return <Sidebar>{children}</Sidebar>;
}

// WRONG: Using loading.tsx without Suspense boundary
// loading.tsx IS the Suspense fallback — it works automatically

// CORRECT: Just create loading.tsx — Next.js wraps page in Suspense automatically
```

## Gotchas
- Root layout (`app/layout.tsx`) is REQUIRED — it wraps all pages
- Nested layouts persist across navigations within their segment
- `loading.tsx` is automatically wrapped in `<Suspense>` by Next.js
- `error.tsx` must be a client component (`"use client"`) — it uses `reset()` which is client-side
- `error.tsx` catches errors in its segment and all nested segments
- Route groups `(name)` organize code without affecting URLs
- Layouts don't receive `searchParams` — only pages do
- Use `template.tsx` instead of `layout.tsx` when you need a new instance on every navigation

## Related
- typescript/web/nextjs/app-router.md
- typescript/web/nextjs/data-fetching.md
- typescript/web/react/error-boundaries.md
