---
id: "typescript-web-nextjs-middleware"
title: "Next.js Middleware"
language: "typescript"
category: "web"
subcategory: "middleware"
tags: ["nextjs", "middleware", "auth", "redirect", "rewrite"]
version: "14+"
retrieval_hint: "Next.js middleware authentication redirect rewrite"
last_verified: "2026-05-24"
confidence: "high"
---

# Next.js Middleware

## When to Use
- Authentication checks before page renders
- URL rewrites and redirects
- A/B testing
- Geolocation-based routing

## Standard Pattern

```typescript
// middleware.ts (root of project)
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value;
  const isAuthenticated = !!token;

  // Protected routes
  if (request.nextUrl.pathname.startsWith('/dashboard')) {
    if (!isAuthenticated) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }

  // Redirect authenticated users away from login
  if (request.nextUrl.pathname === '/login' && isAuthenticated) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Add headers
  const response = NextResponse.next();
  response.headers.set('x-request-id', crypto.randomUUID());
  return response;
}

export const config = {
  matcher: ['/dashboard/:path*', '/login'],
};

// Advanced: Rewrite API proxy
export function middleware(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith('/api/')) {
    const url = new URL(request.nextUrl.pathname, 'https://api.example.com');
    return NextResponse.rewrite(url);
  }
}
```

## Common Mistakes

```typescript
// WRONG: Using Node.js APIs in middleware
import { readFileSync } from 'fs';  // Error: Edge runtime!

// CORRECT: Use Web APIs only
const token = request.cookies.get('token')?.value;

// WRONG: Not using matcher (runs on every request)
export function middleware(request: NextRequest) {
  // Runs on ALL requests — performance impact!
}

// CORRECT: Use matcher to limit scope
export const config = {
  matcher: ['/dashboard/:path*', '/api/:path*'],
};

// WRONG: Matcher missing trailing path wildcard
export const config = {
  matcher: ['/dashboard'],  // Only matches /dashboard exactly, not /dashboard/settings
};

// CORRECT: Use :path* to match nested routes
export const config = {
  matcher: ['/dashboard/:path*'],
};
```

## Gotchas
- Middleware runs on the Edge Runtime — no Node.js APIs
- Use `request.cookies` for cookie access
- `NextResponse.redirect()` for redirects
- `NextResponse.rewrite()` for URL rewrites
- `NextResponse.next()` to continue to the page
- `config.matcher` limits which routes trigger middleware
- Middleware runs before the page renders

## Related
- typescript/web/nextjs/app-router.md
- typescript/web/nextjs/server-actions.md
