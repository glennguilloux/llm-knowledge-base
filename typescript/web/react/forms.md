---
id: "typescript-web-react-forms"
title: "React Forms: Controlled Components and react-hook-form"
language: "typescript"
category: "web"
subcategory: "frontend"
tags: ["react", "forms", "controlled", "hook-form", "validation", "input"]
version: "5.0+"
retrieval_hint: "React forms controlled component react-hook-form validation input handleSubmit"
last_verified: "2026-05-22"
confidence: "high"
---

# React Forms: Controlled Components and react-hook-form

## When to Use
- Simple forms with few fields: controlled components
- Complex forms with validation, dynamic fields, or performance concerns: react-hook-form
- Forms requiring real-time validation feedback
- Multi-step forms with shared state

## Standard Pattern

```tsx
// --- Controlled Component (simple forms) ---
import { useState, type FormEvent } from "react";

interface LoginForm {
  email: string;
  password: string;
}

function ControlledForm() {
  const [form, setForm] = useState<LoginForm>({ email: "", password: "" });
  const [errors, setErrors] = useState<Partial<LoginForm>>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    // Clear error on change
    if (errors[e.target.name as keyof LoginForm]) {
      setErrors((prev) => ({ ...prev, [e.target.name]: undefined }));
    }
  };

  const validate = (): boolean => {
    const newErrors: Partial<LoginForm> = {};
    if (!form.email.includes("@")) newErrors.email = "Invalid email";
    if (form.password.length < 8) newErrors.password = "Min 8 characters";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (validate()) {
      console.log("Submit:", form);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <input name="email" value={form.email} onChange={handleChange} placeholder="Email" />
        {errors.email && <span className="error">{errors.email}</span>}
      </div>
      <div>
        <input name="password" type="password" value={form.password} onChange={handleChange} />
        {errors.password && <span className="error">{errors.password}</span>}
      </div>
      <button type="submit">Login</button>
    </form>
  );
}

// --- react-hook-form (complex forms) ---
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const schema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  email: z.string().email("Invalid email"),
  age: z.number().min(0).max(150),
  tags: z.array(z.string()).min(1, "At least one tag"),
});

type FormData = z.infer<typeof schema>;

function HookForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
    watch,
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", email: "", age: 0, tags: [] },
  });

  const onSubmit = async (data: FormData) => {
    await fetch("/api/users", { method: "POST", body: JSON.stringify(data) });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register("name")} placeholder="Name" />
      {errors.name && <span>{errors.name.message}</span>}

      <input {...register("email")} placeholder="Email" />
      {errors.email && <span>{errors.email.message}</span>}

      <input type="number" {...register("age", { valueAsNumber: true })} />
      {errors.age && <span>{errors.age.message}</span>}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Submitting..." : "Submit"}
      </button>
    </form>
  );
}
```

## Common Mistakes

```tsx
// WRONG: Uncontrolled input with value but no onChange
<input value={form.email} />  // Read-only, React warning

// CORRECT: Add onChange handler
<input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />

// WRONG: Updating state on every keystroke without debounce (expensive validation)
const handleChange = (e) => {
  setForm({ ...form, [e.target.name]: e.target.value });
  validateForm();  // Runs on every keystroke!
};

// CORRECT: Debounce validation or validate on blur/submit
const handleChange = (e) => {
  setForm({ ...form, [e.target.name]: e.target.value });
};

// WRONG: Not preventing default form submission
<form onSubmit={handleSubmit}>  // Page reloads!

// CORRECT: Prevent default
<form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>

// WRONG: Using value={undefined} for controlled input
<input value={undefined} />  // Switches to uncontrolled

// CORRECT: Use empty string as default
<input value={form.email ?? ""} />
```

## Gotchas
- Controlled components re-render on every keystroke — use react-hook-form for performance
- `register()` from react-hook-form handles `onChange`, `ref`, `name` — don't add your own
- `valueAsNumber` in register converts string input to number
- `zodResolver` integrates Zod schema validation with react-hook-form
- `formState.errors` is only populated after submission (or with `mode: "onChange"`)
- Use `watch()` to observe specific fields without re-rendering the entire form
- `setValue` programmatic updates work with react-hook-form — useful for async data loading
- For file inputs, use `register("file")` without `value` (file inputs are always uncontrolled)

## Related
- typescript/web/react/hooks.md
- typescript/web/react/state.md
- typescript/web/react/error-boundaries.md
