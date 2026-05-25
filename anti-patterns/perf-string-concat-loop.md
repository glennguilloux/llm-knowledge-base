---
id: "anti-patterns-perf-string-concat-loop"
title: "Performance Anti-Pattern: String Concatenation in Loops"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "performance", "strings", "concatenation", "quadratic"]
version: "n/a"
retrieval_hint: "string concatenation loop O(n^2) quadratic StringBuilder StringIO join append"
last_verified: "2026-05-24"
confidence: "high"
---

# Performance Anti-Pattern: String Concatenation in Loops

## When to Use
- Building large strings in loops (CSV, SQL, logs, reports)
- Reviewing code that generates output from data
- Training LLMs to write efficient string operations
- Debugging slow loops that process text

## Standard Pattern

```python
# WRONG: O(n^2) — creates new string object on every iteration
result = ""
for i in range(100000):
    result += f"Line {i}\n"  # Each += copies the entire existing string

# CORRECT: Use join (O(n) — single allocation)
lines = []
for i in range(100000):
    lines.append(f"Line {i}\n")
result = "".join(lines)

# CORRECT: Use StringIO for many appends (O(n) — buffered)
from io import StringIO
buffer = StringIO()
for i in range(100000):
    buffer.write(f"Line {i}\n")
result = buffer.getvalue()

# CORRECT: Generator with join (memory efficient)
result = "".join(f"Line {i}\n" for i in range(100000))
```

```java
// WRONG: O(n^2) — String is immutable, each + creates new String
String result = "";
for (int i = 0; i < 100000; i++) {
    result += "Line " + i + "\n";  // Allocates new string each time
}

// CORRECT: StringBuilder (O(n) — mutable buffer)
StringBuilder sb = new StringBuilder();
for (int i = 0; i < 100000; i++) {
    sb.append("Line ").append(i).append("\n");
}
String result = sb.toString();
```

```go
// WRONG: O(n^2) — strings are immutable, each + copies
result := ""
for i := 0; i < 100000; i++ {
    result += fmt.Sprintf("Line %d\n", i)
}

// CORRECT: strings.Builder (O(n) — internal buffer)
var sb strings.Builder
for i := 0; i < 100000; i++ {
    fmt.Fprintf(&sb, "Line %d\n", i)
}
result := sb.String()

// CORRECT: Pre-allocate capacity
var sb strings.Builder
sb.Grow(100000 * 20)  // Estimate total size
for i := 0; i < 100000; i++ {
    fmt.Fprintf(&sb, "Line %d\n", i)
}
```

```javascript
// WRONG: O(n^2) — strings are immutable in JS too
let result = "";
for (let i = 0; i < 100000; i++) {
    result += `Line ${i}\n`;
}

// CORRECT: Array join (O(n) — single allocation)
const lines = [];
for (let i = 0; i < 100000; i++) {
    lines.push(`Line ${i}\n`);
}
const result = lines.join("");

// CORRECT: Functional approach
const result = Array.from({ length: 100000 }, (_, i) => `Line ${i}\n`).join("");
```

```csharp
// WRONG: O(n^2) — String is immutable in C#
string result = "";
for (int i = 0; i < 100000; i++) {
    result += $"Line {i}\n";  // Allocates new string each time
}

// CORRECT: StringBuilder (O(n) — mutable buffer)
var sb = new StringBuilder(100000 * 20);  // Pre-allocate
for (int i = 0; i < 100000; i++) {
    sb.AppendLine($"Line {i}");
}
string result = sb.ToString();
```

```rust
// WRONG: O(n^2) — String concatenation with +
let mut result = String::new();
for i in 0..100_000 {
    result += &format!("Line {}\n", i);  // Reallocates
}

// CORRECT: push_str (append in-place)
let mut result = String::new();
for i in 0..100_000 {
    result.push_str(&format!("Line {}\n", i));
}

// CORRECT: Collect iterator (idiomatic Rust)
let result: String = (0..100_000)
    .map(|i| format!("Line {}\n", i))
    .collect();
```

## Common Mistakes
String concatenation in loops is O(n²) because strings are immutable in most languages. Each `+=` or `+` allocates a new string and copies the entire existing content. With 100,000 iterations, this means ~100,000 allocations and ~5 billion character copies. The fix is always the same: accumulate parts in a list/array, then join once, or use a mutable string builder. The pattern is so common that every major language has a solution: `StringBuilder` (Java, C#), `strings.Builder` (Go), `join()` (Python, JS), `collect()` (Rust).

## Gotchas
- Python `+=` on strings is O(n²) due to immutability — use `"".join(list)` or `StringIO`
- Java's `+` on strings compiles to `StringBuilder` in simple cases — but in loops it does NOT
- Go's `+=` on strings copies the entire string each time — use `strings.Builder` with `Grow()` for best performance
- JavaScript engines (V8) sometimes optimize `+=` in loops — but it's unreliable and version-dependent
- C# string interpolation `$"..."` creates a new string — use `StringBuilder.Append` + `AppendFormat` in loops
- Rust's `format!()` allocates a new `String` — use `write!()` to a pre-allocated buffer
- For CSV generation, always use a library (Python's `csv` module) — it handles escaping and buffering correctly
- Benchmark with realistic data sizes — the difference is negligible below ~100 concatenations

## Related
- anti-patterns/performance-antipatterns.md
- python/stdlib/file-io.md
- typescript/stdlib/string-operations.md
- anti-patterns/perf-sync-in-async.md
