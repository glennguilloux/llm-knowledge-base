---
id: "typescript-state-zustand-patterns"
title: "Zustand State Management Patterns"
language: "typescript"
category: "web"
subcategory: "state-management"
tags: ["zustand", "state", "store", "global", "react", "typescript"]
version: "5.0+"
retrieval_hint: "Zustand store state management create persist middleware TypeScript"
last_verified: "2026-05-24"
confidence: "high"
---

# Zustand State Management Patterns

## When to Use
- Global state that multiple components need (auth, theme, cart)
- Replacing Redux for simpler state management
- State that persists across page navigations
- Complex state with async actions (API calls, side effects)

## Standard Pattern

```typescript
import { create } from "zustand";
import { persist, devtools } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

// --- Basic store ---
interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
}

const useAuthStore = create<AuthState>()((set) => ({
  user: null,
  token: null,
  isLoading: false,

  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) throw new Error("Login failed");
      const { user, token } = await res.json();
      set({ user, token, isLoading: false });
    } catch {
      set({ isLoading: false });
      throw new Error("Login failed");
    }
  },

  logout: () => set({ user: null, token: null }),
  setUser: (user) => set({ user }),
}));

// --- With persistence ---
interface CartState {
  items: CartItem[];
  addItem: (item: CartItem) => void;
  removeItem: (id: string) => void;
  clearCart: () => void;
  total: () => number;
}

const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      addItem: (item) =>
        set((state) => {
          const existing = state.items.find((i) => i.id === item.id);
          if (existing) {
            return { items: state.items.map((i) => (i.id === item.id ? { ...i, qty: i.qty + 1 } : i)) };
          }
          return { items: [...state.items, item] };
        }),
      removeItem: (id) =>
        set((state) => ({ items: state.items.filter((i) => i.id !== id) })),
      clearCart: () => set({ items: [] }),
      total: () => get().items.reduce((sum, i) => sum + i.price * i.qty, 0),
    }),
    { name: "cart-storage" }
  )
);

// --- Component usage ---
function CartButton() {
  const itemCount = useCartStore((s) => s.items.length);  // Only re-renders when items.length changes
  const clearCart = useCartStore((s) => s.clearCart);

  return (
    <div>
      <span>Cart ({itemCount})</span>
      <button onClick={clearCart}>Clear</button>
    </div>
  );
}

// --- With immer (for complex nested updates) ---
interface TreeState {
  nodes: Record<string, Node>;
  updateNode: (id: string, updates: Partial<Node>) => void;
}

const useTreeStore = create<TreeState>()(
  immer((set) => ({
    nodes: {},
    updateNode: (id, updates) =>
      set((state) => {
        Object.assign(state.nodes[id], updates);  // Direct mutation with immer
      }),
  }))
);
```

## Common Mistakes

```typescript
// WRONG: Subscribing to entire store (re-renders on any change)
function Component() {
  const store = useAuthStore();  // Re-renders when ANY field changes
  return <div>{store.user?.name}</div>;
}

// CORRECT: Select only what you need
function Component() {
  const userName = useAuthStore((s) => s.user?.name);  // Only re-renders when user.name changes
  return <div>{userName}</div>;
}

// WRONG: Using store state in useEffect without selector
useEffect(() => {
  const user = useAuthStore.getState().user;  // Not reactive
  if (user) loadData(user.id);
}, []);

// CORRECT: Subscribe to specific state
const user = useAuthStore((s) => s.user);
useEffect(() => {
  if (user) loadData(user.id);
}, [user]);

// WRONG: Mutating state directly
const store = useAuthStore.getState();
store.user = newUser;  // Doesn't trigger re-render!

// CORRECT: Use set() to update state
useAuthStore.setState({ user: newUser });

// WRONG: Not using devtools in development
const useStore = create((set) => ({ ... }));  // No Redux DevTools support

// CORRECT: Wrap with devtools middleware
const useStore = create(devtools((set) => ({ ... })));
```

## Gotchas
- Selector functions (`useStore(s => s.field)`) prevent unnecessary re-renders
- `getState()` reads state outside React (not reactive); `useStore()` reads inside components (reactive)
- Zustand stores are plain JavaScript — no providers needed
- `persist` middleware stores to localStorage by default — configure `storage` for other backends
- `immer` middleware lets you mutate the draft state directly — useful for nested updates
- Middleware is composable: `create(devtools(persist(immer(...))))` 
- `set()` accepts a partial state — it's merged, not replaced
- Use `shallow` from `zustand/shallow` for selecting multiple fields without re-render

## Real-World Example

### Full Store with Auth, API Cache, and Optimistic Updates

```typescript
import { create } from "zustand";
import { shallow } from "zustand/shallow";

interface User {
  id: number;
  name: string;
  email: string;
}

interface AppState {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  // Actions
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  updateProfile: (data: Partial<User>) => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  user: null,
  token: null,
  loading: false,
  error: null,

  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) throw new Error("Invalid credentials");
      const { user, token } = await res.json();
      set({ user, token, loading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Login failed",
        loading: false,
      });
    }
  },

  logout: () => set({ user: null, token: null, error: null }),

  updateProfile: async (data) => {
    const { token, user } = get();
    if (!token || !user) return;
    // Optimistic update
    set({ user: { ...user, ...data } });
    try {
      const res = await fetch(`/api/users/${user.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Update failed");
      const updated = await res.json();
      set({ user: updated });
    } catch (err) {
      // Rollback on failure
      set({ user, error: err instanceof Error ? err.message : "Update failed" });
    }
  },
}));

// Usage: select multiple fields without extra re-renders
function UserProfile() {
  const { user, loading } = useAppStore(
    (s) => ({ user: s.user, loading: s.loading }),
    shallow
  );
  if (loading) return <Spinner />;
  return <div>{user?.name}</div>;
}
```

## Related
- typescript/web/react/context.md
- typescript/web/react/state.md
- typescript/web/react/hooks.md
