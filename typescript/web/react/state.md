---
id: "typescript-web-react-state"
title: "React State Management"
language: "typescript"
category: "web"
subcategory: "react"
tags: ["react", "state", "useState", "useReducer", "zustand", "context"]
version: "18+"
retrieval_hint: "React state management useState useReducer Zustand context"
last_verified: "2026-05-22"
confidence: "high"
---

# React State Management

## When to Use
- Managing component state
- Sharing state between components
- Complex state logic
- Global application state

## Standard Pattern

```typescript
// useState - simple state
function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>;
}

// useReducer - complex state logic
interface State {
  items: Item[];
  loading: boolean;
  error: string | null;
}

type Action =
  | { type: 'LOADING' }
  | { type: 'SUCCESS'; payload: Item[] }
  | { type: 'ERROR'; payload: string };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'LOADING':
      return { ...state, loading: true, error: null };
    case 'SUCCESS':
      return { items: action.payload, loading: false, error: null };
    case 'ERROR':
      return { ...state, loading: false, error: action.payload };
  }
}

function ItemList() {
  const [state, dispatch] = useReducer(reducer, {
    items: [],
    loading: false,
    error: null,
  });

  useEffect(() => {
    dispatch({ type: 'LOADING' });
    fetchItems()
      .then(items => dispatch({ type: 'SUCCESS', payload: items }))
      .catch(err => dispatch({ type: 'ERROR', payload: err.message }));
  }, []);

  if (state.loading) return <p>Loading...</p>;
  if (state.error) return <p>Error: {state.error}</p>;
  return <ul>{state.items.map(item => <li key={item.id}>{item.name}</li>)}</ul>;
}

// Zustand - lightweight global state
import { create } from 'zustand';

interface TodoStore {
  todos: Todo[];
  addTodo: (text: string) => void;
  toggleTodo: (id: string) => void;
}

const useTodoStore = create<TodoStore>((set) => ({
  todos: [],
  addTodo: (text) => set((state) => ({
    todos: [...state.todos, { id: crypto.randomUUID(), text, done: false }],
  })),
  toggleTodo: (id) => set((state) => ({
    todos: state.todos.map(todo =>
      todo.id === id ? { ...todo, done: !todo.done } : todo
    ),
  })),
}));

// Usage
function TodoList() {
  const todos = useTodoStore(state => state.todos);
  const addTodo = useTodoStore(state => state.addTodo);
  const toggleTodo = useTodoStore(state => state.toggleTodo);

  return (
    <ul>
      {todos.map(todo => (
        <li key={todo.id} onClick={() => toggleTodo(todo.id)}>
          {todo.done ? '✓' : '○'} {todo.text}
        </li>
      ))}
    </ul>
  );
}
```

## Common Mistakes

```typescript
// WRONG: Mutating state directly
const [items, setItems] = useState([]);
items.push(newItem);  // Mutation!
setItems(items);  // No re-render!

// CORRECT: Create new array
setItems(prev => [...prev, newItem]);

// WRONG: Storing derived state
const [items, setItems] = useState([]);
const [count, setCount] = useState(0);  // Redundant!

// CORRECT: Derive from existing state
const [items, setItems] = useState([]);
const count = items.length;  // Derived value
```

## Gotchas
- `useState` setter can take a function for lazy initialization
- `useReducer` is better for complex state with multiple sub-values
- Zustand is simpler than Redux for most use cases
- Context re-renders all consumers on change — use Zustand for performance
- Always create new objects/arrays when updating state
- Use `React.memo()` to prevent unnecessary re-renders
- `useCallback` and `useMemo` for expensive computations

## Related
- typescript/web/react/hooks.md
- typescript/web/nextjs/app-router.md
