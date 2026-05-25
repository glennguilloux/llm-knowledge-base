---
id: "antipatterns-react"
title: "React Anti-Patterns"
language: "typescript"
category: "anti-patterns"
tags: ["antipatterns", "react", "hooks", "components", "common-mistakes"]
version: "n/a"
retrieval_hint: "react common mistakes useEffect dependency derived state prop drilling key re-render"
last_verified: "2026-05-24"
confidence: "high"
---

# React Anti-Patterns

## When to Use
- Reviewing React components for common mistakes
- Training small LLMs to avoid frequent React errors
- Code review checklists for React/Next.js applications
- Onboarding developers new to React hooks

## Standard Pattern

```tsx
// WRONG: Storing derived state (redundant, gets out of sync)
function UserList({ users }) {
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    setFilteredUsers(users.filter(u => u.name.includes(search)));
  }, [users, search]);  // Redundant re-render

  return <div>{filteredUsers.map(u => <p key={u.id}>{u.name}</p>)}</div>;
}

// CORRECT: Compute derived values inline or with useMemo
function UserList({ users }) {
  const [search, setSearch] = useState("");
  const filteredUsers = useMemo(
    () => users.filter(u => u.name.includes(search)),
    [users, search]
  );

  return <div>{filteredUsers.map(u => <p key={u.id}>{u.name}</p>)}</div>;
}

// WRONG: useEffect with missing dependency
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetchUser(userId).then(setUser);
  }, []);  // Missing userId — stale closure, fetches only once

  return user ? <div>{user.name}</div> : <Spinner />;
}

// CORRECT: Include all dependencies
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    let cancelled = false;
    fetchUser(userId).then(data => {
      if (!cancelled) setUser(data);
    });
    return () => { cancelled = true; };  // Cleanup for stale requests
  }, [userId]);

  return user ? <div>{user.name}</div> : <Spinner />;
}

// WRONG: Prop drilling through 5 levels
function App() {
  const [theme, setTheme] = useState("dark");
  return <Layout theme={theme} setTheme={setTheme} />;
}
function Layout({ theme, setTheme }) {
  return <Header theme={theme} setTheme={setTheme} />;
}
function Header({ theme, setTheme }) {
  return <Nav theme={theme} setTheme={setTheme} />;
}
function Nav({ theme, setTheme }) {
  return <ThemeToggle theme={theme} setTheme={setTheme} />;
}

// CORRECT: Use Context for deeply shared state
const ThemeContext = createContext();
function App() {
  const [theme, setTheme] = useState("dark");
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      <Layout />
    </ThemeContext.Provider>
  );
}
function ThemeToggle() {
  const { theme, setTheme } = useContext(ThemeContext);
  return <button onClick={() => setTheme(t => t === "dark" ? "light" : "dark")} />;
}

// WRONG: Inline object/function in JSX (new reference every render, causes re-renders)
function Parent() {
  return <Child style={{ color: "red" }} onClick={() => console.log("clicked")} />;
}

// CORRECT: Define outside or memoize
const childStyle = { color: "red" };
function Parent() {
  const handleClick = useCallback(() => console.log("clicked"), []);
  return <Child style={childStyle} onClick={handleClick} />;
}

// WRONG: Not using key in .map() (React can't track items)
function TodoList({ todos }) {
  return todos.map(todo => <TodoItem todo={todo} />);  // Warning in console
}

// CORRECT: Use stable, unique key
function TodoList({ todos }) {
  return todos.map(todo => <TodoItem key={todo.id} todo={todo} />);
}

// WRONG: Fetching in useEffect without cleanup (race condition)
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then(r => r.json())
      .then(setUser);
    // No cleanup — stale response can overwrite fresh data
  }, [userId]);

  return user ? <div>{user.name}</div> : <Spinner />;
}

// CORRECT: AbortController for cleanup
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`/api/users/${userId}`, { signal: controller.signal })
      .then(r => r.json())
      .then(data => setUser(data))
      .catch(e => { if (e.name !== "AbortError") throw e; });
    return () => controller.abort();
  }, [userId]);

  return user ? <div>{user.name}</div> : <Spinner />;
}

// WRONG: Mutating state directly
function Counter() {
  const [count, setCount] = useState(0);
  const increment = () => { count += 1; };  // No re-render
  return <button onClick={increment}>{count}</button>;
}

// CORRECT: Use setter function
function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

## Common Mistakes
The most damaging React anti-patterns are storing derived state (redundant, gets out of sync), `useEffect` with missing dependencies (stale closures), and inline objects in JSX (new reference every render triggers child re-renders). Prop drilling through many levels makes code hard to refactor. Not using `key` in `.map()` causes React to re-render entire lists.

## Gotchas
- `useEffect` dependencies must include ALL values from outer scope used inside the effect
- Derived state should be computed during render, not stored in `useState` — use `useMemo` for expensive computations
- `key` must be stable and unique — never use array index if items can reorder
- Inline objects `{{}}` create a new reference every render — define outside component or memoize
- `useCallback`/`useMemo` are optimizations, not requirements — use them for referential stability, not every function
- Always clean up async effects (`AbortController`, cancelled flag) to prevent race conditions
- Context changes re-render ALL consumers — split contexts for values that change at different rates

## Related
- typescript/web/react/hooks.md
- typescript/web/react/state.md
- typescript/web/react/performance.md
- anti-patterns/performance-antipatterns.md
