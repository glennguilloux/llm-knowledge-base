---
id: "typescript-web-prisma-drizzle"
title: "Database ORM Patterns: Prisma and Drizzle"
language: "typescript"
category: "db"
tags: ["prisma", "drizzle", "orm", "database", "query", "migration", "postgresql"]
version: "5.0+"
retrieval_hint: "prisma drizzle ORM database query migration PostgreSQL schema type-safe"
last_verified: "2026-05-24"
confidence: "high"
---

# Database ORM Patterns: Prisma and Drizzle

## When to Use
- **Prisma**: Full-featured ORM with migration system, ideal for rapid development
- **Drizzle**: Lightweight, SQL-like ORM for developers who want more control
- Type-safe database queries in TypeScript applications
- Schema management and migrations

## Standard Pattern

```typescript
// --- Prisma ---

// schema.prisma
// datasource db {
//   provider = "postgresql"
//   url      = env("DATABASE_URL")
// }
// generator client {
//   provider = "prisma-client-js"
// }
// model User {
//   id    Int    @id @default(autoincrement())
//   name  String
//   email String @unique
//   posts Post[]
// }
// model Post {
//   id       Int    @id @default(autoincrement())
//   title    String
//   content  String
//   author   User   @relation(fields: [authorId], references: [id])
//   authorId Int
// }

import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

// Create
const user = await prisma.user.create({
  data: { name: "Alice", email: "alice@example.com" },
});

// Read with relations
const userWithPosts = await prisma.user.findUnique({
  where: { id: 1 },
  include: { posts: true },
});

// Update
const updated = await prisma.user.update({
  where: { id: 1 },
  data: { name: "Bob" },
});

// Delete
await prisma.user.delete({ where: { id: 1 } });

// Transaction
const [user, post] = await prisma.$transaction([
  prisma.user.create({ data: { name: "Alice", email: "a@b.com" } }),
  prisma.post.create({ data: { title: "Hello", authorId: 1 } }),
]);


// --- Drizzle ---

import { drizzle } from "drizzle-orm/node-postgres";
import { pgTable, serial, text, integer } from "drizzle-orm/pg-core";
import { eq } from "drizzle-orm";

// Schema definition
export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  email: text("email").notNull().unique(),
});

export const posts = pgTable("posts", {
  id: serial("id").primaryKey(),
  title: text("title").notNull(),
  content: text("content").notNull(),
  authorId: integer("author_id").references(() => users.id),
});

// Usage
const db = drizzle(process.env.DATABASE_URL!);

// Insert
const user = await db.insert(users).values({
  name: "Alice",
  email: "alice@example.com",
}).returning();

// Select with filter
const alice = await db.select().from(users).where(eq(users.email, "alice@example.com"));

// Join
const results = await db
  .select()
  .from(users)
  .leftJoin(posts, eq(users.id, posts.authorId));

// Update
await db.update(users).set({ name: "Bob" }).where(eq(users.id, 1));

// Delete
await db.delete(users).where(eq(users.id, 1));
```

## Common Mistakes

```typescript
// WRONG: N+1 query problem with Prisma
const users = await prisma.user.findMany();
for (const user of users) {
  const posts = await prisma.post.findMany({
    where: { authorId: user.id },  // N queries!
  });
}

// CORRECT: Use include or joins
const users = await prisma.user.findMany({
  include: { posts: true },  // Single query with join
});

// WRONG: Not using transactions for related operations
await prisma.user.create({ data: { name: "Alice", email: "a@b.com" } });
await prisma.post.create({ data: { title: "Hello", authorId: 1 } });
// If second fails, first is already committed!

// CORRECT: Use transaction
await prisma.$transaction([
  prisma.user.create({ data: { name: "Alice", email: "a@b.com" } }),
  prisma.post.create({ data: { title: "Hello", authorId: 1 } }),
]);

// WRONG: Not handling unique constraint violations
await prisma.user.create({ data: { name: "Alice", email: "existing@example.com" } });
// Throws PrismaClientKnownRequestError

// CORRECT: Handle specific errors
try {
  await prisma.user.create({ data: { name: "Alice", email: "existing@example.com" } });
} catch (err) {
  if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === "P2002") {
    throw new Error("Email already exists");
  }
  throw err;
}

// WRONG: Using Drizzle without .returning()
await db.insert(users).values({ name: "Alice", email: "a@b.com" });
// No way to get the inserted ID!

// CORRECT: Use .returning()
const [user] = await db.insert(users).values({
  name: "Alice",
  email: "a@b.com",
}).returning();
```

## Gotchas
- Prisma Client is generated — run `npx prisma generate` after schema changes
- `prisma.$transaction` accepts an array (parallel) or a callback (interactive)
- Drizzle generates SQL that matches your schema — inspect with `.toSQL()` for debugging
- Prisma uses `@relation` for joins; Drizzle uses explicit `.leftJoin()` / `.innerJoin()`
- `findUnique` throws if not found; `findFirst` returns null — choose based on your error handling
- Drizzle's `eq()`, `gt()`, `lt()` are type-safe — compile errors for wrong column types
- Always use `.returning()` in Drizzle when you need the inserted/updated row

## Related
- typescript/web/express-server.md
- db/postgres/indexes.md
- db/postgres/transactions.md
