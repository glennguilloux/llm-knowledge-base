---
id: "typescript-web-trpc-patterns"
title: "tRPC Type-Safe API Patterns"
language: "typescript"
category: "web"
subcategory: "api-framework"
tags: ["trpc", "type-safe", "api", "rpc", "typescript", "end-to-end"]
version: "5.0+"
retrieval_hint: "tRPC type-safe API RPC end-to-end TypeScript procedure router query mutation"
last_verified: "2026-05-22"
confidence: "high"
---

# tRPC Type-Safe API Patterns

## When to Use
- Full-stack TypeScript projects wanting end-to-end type safety
- Replacing REST/GraphQL with zero-codegen type-safe APIs
- Next.js apps with API routes that share types with the frontend
- Teams that want autocompletion from server to client

## Standard Pattern

```typescript
// --- server/trpc.ts: Initialize tRPC ---
import { initTRPC, TRPCError } from "@trpc/server";
import { z } from "zod";

const t = initTRPC.context<Context>().create();

export const router = t.router;
export const publicProcedure = t.procedure;
export const middleware = t.middleware;

// Auth middleware
const isAuthed = middleware(({ ctx, next }) => {
  if (!ctx.session?.user) {
    throw new TRPCError({ code: "UNAUTHORIZED" });
  }
  return next({ ctx: { user: ctx.session.user } });
});

export const protectedProcedure = t.procedure.use(isAuthed);

// --- server/routers/user.ts ---
export const userRouter = router({
  list: publicProcedure
    .input(z.object({ page: z.number().default(0), limit: z.number().max(100).default(20) }))
    .query(async ({ input }) => {
      return db.user.findMany({ skip: input.page * input.limit, take: input.limit });
    }),

  byId: publicProcedure
    .input(z.object({ id: z.number() }))
    .query(async ({ input }) => {
      const user = await db.user.findUnique({ where: { id: input.id } });
      if (!user) throw new TRPCError({ code: "NOT_FOUND" });
      return user;
    }),

  create: protectedProcedure
    .input(z.object({ name: z.string().min(1), email: z.string().email() }))
    .mutation(async ({ input, ctx }) => {
      return db.user.create({ data: { ...input, createdById: ctx.user.id } });
    }),

  delete: protectedProcedure
    .input(z.object({ id: z.number() }))
    .mutation(async ({ input }) => {
      await db.user.delete({ where: { id: input.id } });
      return { success: true };
    }),
});

// --- server/root.ts ---
export const appRouter = router({
  user: userRouter,
  post: postRouter,
});

export type AppRouter = typeof appRouter;

// --- Client usage (React) ---
"use client";
import { trpc } from "@/lib/trpc";

function UserList() {
  const { data: users, isLoading } = trpc.user.list.useQuery({ page: 0, limit: 20 });
  const createUser = trpc.user.create.useMutation({
    onSuccess: () => trpc.user.list.invalidate(),
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      {users?.map((user) => (
        <div key={user.id}>{user.name}</div>
      ))}
      <button onClick={() => createUser.mutate({ name: "Alice", email: "a@b.com" })}>
        Add User
      </button>
    </div>
  );
}

// --- Setup with Next.js ---
// app/api/trpc/[trpc]/route.ts
import { fetchRequestHandler } from "@trpc/server/adapters/fetch";
import { appRouter } from "@/server/root";

export const GET = (req: Request) =>
  fetchRequestHandler({ endpoint: "/api/trpc", req, router: appRouter, createContext });

export const POST = GET;
```

## Common Mistakes

```typescript
// WRONG: Not exporting the router type
const appRouter = router({ user: userRouter });
// Client can't infer types!

// CORRECT: Export the type
export type AppRouter = typeof appRouter;

// WRONG: Using tRPC for file uploads (not designed for it)
trpc.upload.useMutation(formData)  // Not supported

// CORRECT: Use regular API route for file uploads

// WRONG: Not invalidating queries after mutation
const createUser = trpc.user.create.useMutation();
// List doesn't update after creating a user!

// CORRECT: Invalidate related queries
const createUser = trpc.user.create.useMutation({
  onSuccess: () => trpc.user.list.invalidate(),
});

// WRONG: Calling procedures server-side through HTTP
const users = await fetch("/api/trpc/user.list");  // Unnecessary HTTP call

// CORRECT: Call the router directly server-side
import { appRouter } from "./root";
const caller = appRouter.createCaller(ctx);
const users = await caller.user.list({ page: 0 });
```

## Gotchas
- `AppRouter` type must be exported and imported on the client for type inference
- Input validation uses Zod schemas — same as API validation
- `useQuery` for GET-like operations; `useMutation` for POST/PUT/DELETE
- `invalidate()` triggers a refetch of the specified query
- `TRPCError` maps to HTTP status codes (NOT_FOUND → 404, UNAUTHORIZED → 401)
- Server-side caller (`createCaller`) bypasses HTTP — use for SSR
- tRPC supports subscriptions via WebSocket for real-time data
- Use `trpc.devtools` for debugging in development

## Related
- typescript/web/zod-validation.md
- typescript/web/nextjs/app-router.md
- typescript/web/express/middleware.md
