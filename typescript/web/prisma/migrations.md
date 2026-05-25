---
id: "typescript-web-prisma-migrations"
title: "Prisma Migrations, Seed Data, and Relations"
language: "typescript"
category: "db"
subcategory: "orm"
tags: ["prisma", "migrations", "seed", "relations", "transactions", "schema"]
version: "5.0+"
retrieval_hint: "Prisma migrations seed relations transactions schema PostgreSQL"
last_verified: "2026-05-24"
confidence: "high"
---

# Prisma Migrations, Seed Data, and Relations

## When to Use
- Database schema management with TypeScript-first ORM
- Seeding development/test databases with initial data
- Complex queries with relations (joins, nested creates)
- Transactional operations that must succeed or fail together

## Standard Pattern

```typescript
// --- prisma/schema.prisma ---
// datasource db {
//   provider = "postgresql"
//   url      = env("DATABASE_URL")
// }
//
// generator client {
//   provider = "prisma-client-js"
// }
//
// model User {
//   id        Int      @id @default(autoincrement())
//   email     String   @unique
//   name      String
//   posts     Post[]
//   profile   Profile?
//   createdAt DateTime @default(now())
//   updatedAt DateTime @updatedAt
// }
//
// model Post {
//   id        Int      @id @default(autoincrement())
//   title     String
//   content   String?
//   published Boolean  @default(false)
//   author    User     @relation(fields: [authorId], references: [id])
//   authorId  Int
//   tags      Tag[]
//   createdAt DateTime @default(now())
// }
//
// model Tag {
//   id    Int    @id @default(autoincrement())
//   name  String @unique
//   posts Post[]
// }

// --- Queries with relations ---
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

// Create with nested relations
async function createUserWithPost() {
  return prisma.user.create({
    data: {
      email: "alice@example.com",
      name: "Alice",
      posts: {
        create: [
          { title: "First Post", content: "Hello world" },
          { title: "Second Post", published: true },
        ],
      },
    },
    include: { posts: true },
  });
}

// Query with filtering and relations
async function getPublishedPosts() {
  return prisma.post.findMany({
    where: { published: true },
    include: {
      author: { select: { id: true, name: true } },
      tags: true,
    },
    orderBy: { createdAt: "desc" },
    take: 20,
  });
}

// Transactions
async function transferFunds(fromId: number, toId: number, amount: number) {
  return prisma.$transaction([
    prisma.account.update({
      where: { id: fromId },
      data: { balance: { decrement: amount } },
    }),
    prisma.account.update({
      where: { id: toId },
      data: { balance: { increment: amount } },
    }),
  ]);
}

// Interactive transaction (access to client)
async function createOrderWithItems(userId: number, items: { productId: number; qty: number }[]) {
  return prisma.$transaction(async (tx) => {
    const order = await tx.order.create({
      data: { userId, total: 0 },
    });

    let total = 0;
    for (const item of items) {
      const product = await tx.product.findUniqueOrThrow({ where: { id: item.productId } });
      await tx.orderItem.create({
        data: { orderId: order.id, productId: item.productId, qty: item.qty, price: product.price },
      });
      total += product.price * item.qty;
    }

    return tx.order.update({
      where: { id: order.id },
      data: { total },
    });
  });
}

// --- Seed script (prisma/seed.ts) ---
async function main() {
  const alice = await prisma.user.upsert({
    where: { email: "alice@example.com" },
    update: {},
    create: {
      email: "alice@example.com",
      name: "Alice",
      posts: { create: [{ title: "Hello World" }] },
    },
  });
  console.log("Seeded:", alice.email);
}

main().catch(console.error).finally(() => prisma.$disconnect());
```

## Common Mistakes

```typescript
// WRONG: Not disconnecting Prisma client
const prisma = new PrismaClient();
// Connection pool exhausted after many requests

// CORRECT: Disconnect or use singleton
const prisma = new PrismaClient();
process.on("beforeExit", () => prisma.$disconnect());

// WRONG: N+1 query (loop with individual queries)
const users = await prisma.user.findMany();
for (const user of users) {
  user.posts = await prisma.post.findMany({ where: { authorId: user.id } });
}

// CORRECT: Use include for eager loading
const users = await prisma.user.findMany({ include: { posts: true } });

// WRONG: Using prisma.user.findUnique without unique field
await prisma.user.findUnique({ where: { name: "Alice" } });  // name is not unique!

// CORRECT: Use findFirst for non-unique fields
await prisma.user.findFirst({ where: { name: "Alice" } });

// WRONG: Not handling PrismaClientKnownRequestError
await prisma.user.create({ data: { email: "alice@test.com" } });
// P2002 error if email already exists — unhandled!

// CORRECT: Catch specific Prisma errors
try {
  await prisma.user.create({ data: { email: "alice@test.com" } });
} catch (e) {
  if (e instanceof Prisma.PrismaClientKnownRequestError && e.code === "P2002") {
    throw new ConflictError("Email already exists");
  }
  throw e;
}
```

## Gotchas
- `npx prisma migrate dev` creates migration + applies it; `npx prisma migrate deploy` only applies
- `include` loads relations; `select` picks specific fields — don't use both on the same relation
- `$transaction([...])` runs all queries in a single DB transaction
- `findUniqueOrThrow` throws if not found (404-friendly)
- Prisma Client is generated from schema — run `npx prisma generate` after schema changes
- `@default(now())` sets value at Prisma level; `@updatedAt` auto-updates on change
- Use `npx prisma db push` for prototyping (no migration files); `migrate dev` for production
- Seed script path is configured in `package.json`: `"prisma": { "seed": "ts-node prisma/seed.ts" }`

## Related
- typescript/web/prisma-drizzle.md
- typescript/web/express/middleware.md
- typescript/web/nextjs/data-fetching.md
