---
id: "typescript-web-react-context"
title: "React Context API for State Sharing"
language: "typescript"
category: "web"
subcategory: "frontend"
tags: ["react", "context", "provider", "consumer", "theme", "global-state"]
version: "5.0+"
retrieval_hint: "React Context API Provider useContext global state theme auth"
last_verified: "2026-05-22"
confidence: "high"
---

# React Context API for State Sharing

## When to Use
- Sharing data across many components without prop drilling (theme, locale, auth)
- App-wide configuration (feature flags, API base URL)
- Avoiding prop drilling deeper than 2-3 levels
- Simple global state that doesn't need Redux/Zustand complexity

## Standard Pattern

```tsx
import { createContext, useContext, useState, useCallback, type ReactNode } from "react";

// --- Theme context ---
interface ThemeContextType {
  theme: "light" | "dark";
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
}

// --- Auth context ---
interface User {
  id: string;
  email: string;
  name: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) throw new Error("Login failed");
      setUser(await res.json());
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    fetch("/api/auth/logout", { method: "POST" });
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

// --- Usage in app ---
function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Layout />
      </AuthProvider>
    </ThemeProvider>
  );
}

function Layout() {
  const { theme, toggleTheme } = useTheme();
  const { user } = useAuth();

  return (
    <div className={theme}>
      <button onClick={toggleTheme}>Toggle Theme</button>
      {user ? <Dashboard /> : <LoginForm />}
    </div>
  );
}
```

## Common Mistakes

```tsx
// WRONG: Context causes re-render of ALL consumers on any change
const DataContext = createContext({ items: [], loading: false });

// Every consumer re-renders when any field changes

// CORRECT: Split contexts or use useMemo
const ItemsContext = createContext<Item[]>([]);
const LoadingContext = createContext(false);

// WRONG: Not handling null context value
const ThemeContext = createContext<ThemeContextType>(null as any);

// CORRECT: Check for null in hook
function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be within ThemeProvider");
  return context;
}

// WRONG: Creating context value without memoization (new object every render)
<ThemeContext.Provider value={{ theme, toggleTheme }}>  // New object = re-render all consumers

// CORRECT: Memoize the value
const value = useMemo(() => ({ theme, toggleTheme }), [theme, toggleTheme]);
<ThemeContext.Provider value={value}>

// WRONG: Using context for frequently changing state (performance)
const MousePositionContext = createContext({ x: 0, y: 0 });
// Mouse moves trigger re-renders of ALL consumers!

// CORRECT: Use context for rarely-changing state, local state for frequent updates
```

## Gotchas
- `createContext(null)` requires null checks in the consumer hook
- Context re-renders all consumers when the value changes — split contexts for different concerns
- `useMemo` on the context value prevents unnecessary re-renders
- Context is NOT a replacement for state management — use Zustand/Redux for complex state
- Providers can be nested — inner providers override outer ones for the same context
- Context works on the server in Next.js App Router — providers must be client components
- `useContext` always reads the nearest provider up the tree
- For TypeScript, always type the context value explicitly (not inferred from default)

## Related
- typescript/web/react/state.md
- typescript/web/react/hooks.md
- typescript/web/react/performance.md
