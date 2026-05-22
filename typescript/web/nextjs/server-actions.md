---
id: "typescript-web-nextjs-server-actions"
title: "Next.js Server Actions"
language: "typescript"
category: "web"
subcategory: "framework"
tags: ["nextjs", "server-actions", "form", "mutation", "server"]
version: "14+"
retrieval_hint: "Next.js server actions form mutation server-side"
last_verified: "2026-05-22"
confidence: "high"
---

# Next.js Server Actions

## When to Use
- Form submissions without API routes
- Server-side data mutations
- Progressive enhancement
- Simplified data flow

## Standard Pattern

```typescript
// app/actions.ts
'use server';

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';

export async function createItem(formData: FormData) {
  const name = formData.get('name') as string;
  const email = formData.get('email') as string;

  // Validate
  if (!name || !email) {
    return { error: 'Name and email are required' };
  }

  // Database operation
  await db.items.create({ data: { name, email } });

  // Revalidate the page to show new data
  revalidatePath('/items');

  // Redirect after success
  redirect('/items');
}

export async function deleteItem(id: string) {
  await db.items.delete({ where: { id } });
  revalidatePath('/items');
}

// app/items/page.tsx - Using server action in form
export default async function ItemsPage() {
  const items = await db.items.findMany();

  return (
    <div>
      <form action={createItem}>
        <input name="name" placeholder="Name" required />
        <input name="email" placeholder="Email" required />
        <button type="submit">Create</button>
      </form>

      <ul>
        {items.map(item => (
          <li key={item.id}>
            {item.name}
            <form action={deleteItem.bind(null, item.id)}>
              <button type="submit">Delete</button>
            </form>
          </li>
        ))}
      </ul>
    </div>
  );
}

// Client component with useActionState
'use client';

import { useActionState } from 'react';
import { createItem } from './actions';

export function CreateItemForm() {
  const [state, formAction, isPending] = useActionState(createItem, null);

  return (
    <form action={formAction}>
      <input name="name" placeholder="Name" required />
      <input name="email" placeholder="Email" required />
      <button type="submit" disabled={isPending}>
        {isPending ? 'Creating...' : 'Create'}
      </button>
      {state?.error && <p className="error">{state.error}</p>}
    </form>
  );
}
```

## Common Mistakes

```typescript
// WRONG: Calling server action from event handler without 'use server'
'use client';
export function Form() {
  const handleClick = async () => {
    await createItem(formData);  // Error: can't call server function from client
  };
}

// CORRECT: Use form action or wrap with 'use server'
// Option 1: Use form action
<form action={createItem}>

// Option 2: Call from form action
const handleSubmit = async (formData: FormData) => {
  'use server';
  await createItem(formData);
};

// WRONG: Not revalidating after mutation
export async function createItem(formData: FormData) {
  await db.items.create({ data: { name: formData.get('name') } });
  // Page shows stale data!
}

// CORRECT: Revalidate path
export async function createItem(formData: FormData) {
  await db.items.create({ data: { name: formData.get('name') } });
  revalidatePath('/items');
}
```

## Gotchas
- Server actions must have `'use server'` directive
- Can be called from form `action` prop or client event handlers
- `revalidatePath()` refreshes the page data after mutation
- `redirect()` should be called after `revalidatePath()`
- Use `useActionState` for pending states and error handling
- Server actions run on the server — can access database directly
- FormData values are always strings

## Real-World Example

### Server Action with Validation, Revalidation, and Optimistic UI

```typescript
"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { z } from "zod";

const TaskSchema = z.object({
  title: z.string().min(1).max(200),
  description: z.string().max(2000).optional(),
  priority: z.enum(["low", "medium", "high"]).default("medium"),
});

export type TaskFormState = {
  errors?: Record<string, string[]>;
  message?: string;
};

export async function createTask(
  prevState: TaskFormState,
  formData: FormData
): Promise<TaskFormState> {
  const parsed = TaskSchema.safeParse({
    title: formData.get("title"),
    description: formData.get("description"),
    priority: formData.get("priority"),
  });

  if (!parsed.success) {
    return { errors: parsed.error.flatten().fieldErrors };
  }

  try {
    await db.insert(tasks).values({
      ...parsed.data,
      userId: getCurrentUser(),
      createdAt: new Date(),
    });
  } catch {
    return { message: "Database error: failed to create task" };
  }

  revalidatePath("/tasks");
  redirect("/tasks");
}

// Client: const [state, formAction, pending] = useActionState(createTask, {});
```

## Related
- typescript/web/nextjs/app-router.md
- typescript/web/nextjs/data-fetching.md
