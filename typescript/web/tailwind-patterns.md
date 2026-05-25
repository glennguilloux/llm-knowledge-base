---
id: "typescript-web-tailwind-patterns"
title: "Tailwind CSS Common Patterns"
language: "typescript"
category: "web"
subcategory: "styling"
tags: ["tailwind", "css", "responsive", "dark-mode", "flexbox", "grid"]
version: "5.0+"
retrieval_hint: "Tailwind CSS responsive dark mode flexbox grid utility classes design"
last_verified: "2026-05-24"
confidence: "high"
---

# Tailwind CSS Common Patterns

## When to Use
- Rapid UI development with utility-first CSS
- Responsive design with breakpoint prefixes
- Dark mode with `dark:` variant
- Consistent spacing, typography, and color systems

## Standard Pattern

```tsx
// --- Responsive layout ---
function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Responsive grid: 1 col on mobile, 2 on tablet, 3 on desktop */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
        <Card />
        <Card />
        <Card />
      </div>
    </div>
  );
}

// --- Card component ---
function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">{title}</h3>
      <div className="text-gray-600 dark:text-gray-300">{children}</div>
    </div>
  );
}

// --- Flexbox patterns ---
function Navbar() {
  return (
    <nav className="flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 border-b">
      <div className="flex items-center gap-4">
        <Logo />
        <span className="text-xl font-bold">App</span>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="ghost">Sign in</Button>
        <Button variant="primary">Sign up</Button>
      </div>
    </nav>
  );
}

// --- Button variants with class-variance-authority ---
import { cva, type VariantProps } from "class-variance-authority";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-500",
        secondary: "bg-gray-200 text-gray-900 hover:bg-gray-300 dark:bg-gray-700 dark:text-white",
        ghost: "hover:bg-gray-100 dark:hover:bg-gray-800",
        destructive: "bg-red-600 text-white hover:bg-red-700",
      },
      size: {
        sm: "h-8 px-3 text-sm",
        md: "h-10 px-4 text-sm",
        lg: "h-12 px-6 text-base",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  }
);

function Button({ variant, size, className, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof buttonVariants>) {
  return <button className={buttonVariants({ variant, size, className })} {...props} />;
}

// --- Form input ---
function Input({ label, error, ...props }: { label: string; error?: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="space-y-1">
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">{label}</label>
      <input
        className={`w-full rounded-md border px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white ${
          error ? "border-red-500" : "border-gray-300"
        }`}
        {...props}
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
```

## Common Mistakes

```tsx
// WRONG: Using arbitrary values everywhere
<div className="w-[347px] h-[892px]">  // Not responsive, not consistent

// CORRECT: Use Tailwind's scale
<div className="w-80 h-[22rem]">  // w-80 = 320px, uses design system

// WRONG: Not supporting dark mode
<div className="bg-white text-black">  // Blinding in dark mode

// CORRECT: Add dark: variants
<div className="bg-white dark:bg-gray-900 text-black dark:text-white">

// WRONG: Inline styles mixed with Tailwind
<div style={{ marginTop: "16px" }} className="p-4">  // Inconsistent

// CORRECT: Use Tailwind for everything
<div className="p-4 mt-4">

// WRONG: Repeating complex class strings
<div className="flex items-center justify-between px-4 py-2 bg-white rounded-lg shadow">
<div className="flex items-center justify-between px-4 py-2 bg-white rounded-lg shadow">

// CORRECT: Extract to component or use @apply in CSS
// components.css: @layer components { .card { @apply flex items-center justify-between px-4 py-2 bg-white rounded-lg shadow; } }
```

## Gotchas
- Responsive prefixes: `sm:` (640px), `md:` (768px), `lg:` (1024px), `xl:` (1280px)
- `dark:` variant uses `prefers-color-scheme` by default — add `class` strategy for toggle
- `hover:`, `focus:`, `active:` are pseudo-class variants
- Tailwind purges unused classes in production — dynamic classes may be purged
- Use `class-variance-authority` (cva) for component variants with TypeScript
- `@apply` in CSS files lets you compose Tailwind utilities into reusable classes
- `tailwind.config.js` `content` array must include all files using Tailwind classes
- Arbitrary values `[value]` work but break the design system — use sparingly

## Related
- typescript/web/react/forms.md
- typescript/web/nextjs/app-router.md
- typescript/web/react/context.md
