---
id: "go-stdlib-strings-builder"
title: "strings.Builder"
language: "go"
category: "stdlib"
tags: ["go", "string", "builder", "concatenation", "performance", "buffer", "strings"]
version: "1.10+"
retrieval_hint: "strings.Builder string concatenation efficient loop WriteString Grow"
last_verified: "2026-05-24"
confidence: "high"
---

# strings.Builder

## When to Use
- Concatenating strings in a loop or hot path
- Building large strings from many small pieces
- Constructing output for HTTP responses, log messages, or templates
- Any scenario where `+` or `+=` on strings causes measurable allocation pressure
- Replacing `bytes.Buffer` when you only need a `string` result

## Standard Pattern

```go
package main

import (
	"fmt"
	"strings"
)

// Basic usage — build a string from parts
func buildGreeting(name string) string {
	var b strings.Builder
	b.WriteString("Hello, ")
	b.WriteString(name)
	b.WriteString("!")
	return b.String()
}

// Pre-allocate with Grow when final size is roughly known
func buildCSV(rows [][]string) string {
	// Estimate: ~20 bytes per cell
	total := 0
	for _, row := range rows {
		for _, cell := range row {
			total += len(cell)
		}
		total += len(row) // commas
	}

	var b strings.Builder
	b.Grow(total)

	for i, row := range rows {
		if i > 0 {
			b.WriteByte('\n')
		}
		for j, cell := range row {
			if j > 0 {
				b.WriteByte(',')
			}
			b.WriteString(cell)
		}
	}
	return b.String()
}

// WriteString, WriteByte, WriteRune, Write — all available
func buildMixed() string {
	var b strings.Builder
	b.WriteString("count=")
	b.WriteByte(':')
	b.WriteRune(' ')
	fmt.Fprintf(&b, "%d", 42) // io.Writer interface
	return b.String()
}

// Reset for reuse (avoids reallocation)
func processLines(lines []string) string {
	var b strings.Builder
	b.Grow(1024)

	for _, line := range lines {
		b.Reset()
		b.WriteString(line)
		b.WriteString("\n")
		// use b.String() or write to another writer
		_ = b.String()
	}
	return ""
}

func main() {
	fmt.Println(buildGreeting("World"))

	csv := buildCSV([][]string{
		{"name", "age", "city"},
		{"Alice", "30", "NYC"},
		{"Bob", "25", "LA"},
	})
	fmt.Println(csv)

	fmt.Println(buildMixed())
}
```

## Common Mistakes

```go
// WRONG: using + in a loop — O(n²) allocations
func joinWords(words []string) string {
	result := ""
	for _, w := range words {
		result += w + " " // allocates a new string each iteration
	}
	return result
}

// CORRECT: use strings.Builder
func joinWords(words []string) string {
	var b strings.Builder
	for _, w := range words {
		b.WriteString(w)
		b.WriteByte(' ')
	}
	return b.String()
}

// WRONG: copying a strings.Builder (it becomes unusable)
var b strings.Builder
b.WriteString("hello")
b2 := b        // b2 is a copy — b is now invalid
_ = b2
// b.WriteString("world") // would panic or corrupt

// CORRECT: pass by pointer if you need to share
func appendTo(b *strings.Builder, s string) {
	b.WriteString(s)
}

// WRONG: calling String() in a hot loop (allocates each time)
var b strings.Builder
for i := 0; i < 1000; i++ {
	b.WriteString("x")
	_ = b.String() // allocates every iteration
}

// CORRECT: call String() once at the end
for i := 0; i < 1000; i++ {
	b.WriteString("x")
}
result := b.String()

// WRONG: forgetting that Builder is not safe for concurrent use
var b strings.Builder
// goroutine 1: b.WriteString("a")
// goroutine 2: b.WriteString("b") // data race!

// CORRECT: use sync.Mutex or separate builders per goroutine
// Or use a bytes.Buffer with a mutex if concurrent writes are needed

// WRONG: using fmt.Sprintf for simple concatenation
func buildKey(prefix, id string) string {
	return fmt.Sprintf("%s:%s", prefix, id) // slower than Builder for many calls
}

// CORRECT: Builder for hot paths, fmt.Sprintf for one-off formatting
func buildKey(prefix, id string) string {
	var b strings.Builder
	b.Grow(len(prefix) + 1 + len(id))
	b.WriteString(prefix)
	b.WriteByte(':')
	b.WriteString(id)
	return b.String()
}
```

## Gotchas
- `strings.Builder` implements `io.Writer`, `io.StringWriter`, and `io.ByteWriter` — you can pass `&b` to `fmt.Fprintf`, `io.Copy`, etc.
- `Grow(n)` pre-allocates at least `n` bytes — calling it once is cheap; calling it repeatedly is not
- `Reset()` clears the builder but keeps the underlying buffer for reuse — useful in tight loops
- `Len()` returns the number of bytes written, not the string length (they're the same for ASCII but differ for multi-byte UTF-8)
- `strings.Builder` cannot be copied after first use — the zero value is ready to use, but `b2 := b` creates a broken copy
- `String()` returns a string that shares the builder's internal buffer — if you call `WriteString` after `String()`, the old string may be corrupted. Call `String()` only when done.
- `Write` appends a byte slice; `WriteByte` appends a single byte; `WriteRune` appends a UTF-8 encoded rune — pick the right one to avoid unnecessary conversions
- For simple joins of a known slice, `strings.Join` is still the best choice — Builder shines when pieces arrive incrementally

## Related
- go/stdlib/slices-maps.md
- go/stdlib/goroutines.md
