---
id: "go-stdlib-slices-maps"
title: "Slices and Maps"
language: "go"
category: "stdlib"
tags: ["go", "slice", "map", "collection", "data-structure", "append", "sync.Map"]
version: "1.21+"
retrieval_hint: "slice map append make capacity range delete sync.Map"
last_verified: "2026-05-22"
confidence: "high"
---

# Slices and Maps

## When to Use
- Working with ordered collections of elements (slices)
- Storing key-value pairs with fast lookup (maps)
- Implementing stacks, queues, or dynamic arrays (slices)
- Building caches, indexes, or sets (maps)
- Concurrent-safe map access (sync.Map)

## Standard Pattern

```go
package main

import (
	"fmt"
	"sync"
)

// --- Slices ---

// Literal and make
s1 := []int{1, 2, 3}              // length 3, capacity 3
s2 := make([]int, 5)               // length 5, capacity 5, zeroed
s3 := make([]int, 0, 10)           // length 0, capacity 10
s4 := make([]int, 3, 10)           // length 3, capacity 10, zeroed

// Append — may or may not allocate
s := []int{1, 2}
s = append(s, 3)                   // [1, 2, 3]
s = append(s, 4, 5, 6)             // [1, 2, 3, 4, 5, 6]
s = append(s, []int{7, 8}...)      // spread operator

// Slice expression — shares backing array
original := []int{0, 1, 2, 3, 4}
sub := original[1:3]               // [1, 2] — shares memory
copy := make([]int, len(original))
n := copy(copy, original)          // independent copy

// Copy with different lengths
src := []int{1, 2, 3}
dst := make([]int, 2)
copy(dst, src)                     // dst = [1, 2], truncated

// Delete element (preserves order)
s = []int{1, 2, 3, 4, 5}
i := 2 // delete index 2 (value 3)
s = append(s[:i], s[i+1:]...)      // [1, 2, 4, 5]

// Delete element (order not preserved)
s = []int{1, 2, 3, 4, 5}
i = 2
s[i] = s[len(s)-1]
s = s[:len(s)-1]                   // [1, 2, 5, 4]

// Filtering without allocation
func filter(vs []string, f func(string) bool) []string {
	result := vs[:0] // reuses backing array
	for _, v := range vs {
		if f(v) {
			result = append(result, v)
		}
	}
	return result
}

// --- Maps ---

// Creation
m1 := map[string]int{"a": 1, "b": 2}
m2 := make(map[string]int, 100) // pre-sized

// Operations
m1["c"] = 3                       // insert/update
val := m1["a"]                     // get (zero value if missing)
val, ok := m1["missing"]           // ok=false, val=0
delete(m1, "b")                    // delete key

// Iteration
for k, v := range m1 {
    fmt.Printf("%s = %d\n", k, v)
}

// Map as set
set := make(map[string]struct{})
set["item"] = struct{}{}
if _, exists := set["item"]; exists {
    fmt.Println("found")
}

// Map of slices (grouping)
users := []string{"alice", "bob", "charlie", "dave"}
byInitial := make(map[byte][]string)
for _, u := range users {
    key := u[0]
    byInitial[key] = append(byInitial[key], u)
}

// --- sync.Map ---

// For concurrent access with many goroutines
var sm sync.Map

sm.Store("key", "value")
sm.Store("count", 42)

if v, ok := sm.Load("key"); ok {
    fmt.Println(v) // "value"
}

sm.Delete("key")

// LoadOrStore — atomic load-or-insert
actual, loaded := sm.LoadOrStore("new", "value")
// loaded=false means "new" was just created with "value"

// Range over all entries
sm.Range(func(key, value any) bool {
    fmt.Printf("%v = %v\n", key, value)
    return true // return false to stop
})
```

## Common Mistakes

```go
// WRONG: append to a sub-slice may corrupt original
original := []int{1, 2, 3, 4, 5}
sub := original[:3]               // shares backing array
sub = append(sub, 99)             // overwrites original[3]!
fmt.Println(original)             // [1, 2, 3, 99, 5]

// CORRECT: copy to break sharing
sub := make([]int, 3)
copy(sub, original[:3])
sub = append(sub, 99)             // independent

// WRONG: iterating map with assumption of order
m := map[string]int{"a": 1, "b": 2, "c": 3}
for k, v := range m {
    fmt.Println(k, v)             // order is random each run
}

// CORRECT: sort keys if order matters
keys := make([]string, 0, len(m))
for k := range m {
    keys = append(keys, k)
}
sort.Strings(keys)
for _, k := range keys {
    fmt.Println(k, m[k])
}

// WRONG: checking map key existence with zero value
val := m["missing"]               // returns 0 — is it missing or actually 0?

// CORRECT: use comma-ok idiom
val, ok := m["missing"]
if !ok {
    // key does not exist
}

// WRONG: nil map panics on write
var m map[string]int
m["key"] = 1                      // panic: assignment to entry in nil map

// CORRECT: initialize before use
m := make(map[string]int)
m["key"] = 1

// WRONG: range variable reused across iterations
s := make([]func(), 3)
for i, v := range []int{1, 2, 3} {
    s[i] = func() { fmt.Println(v) } // all closures capture same v
}
for _, f := range s { f() } // prints 3, 3, 3

// CORRECT: capture loop variable explicitly
for i, v := range []int{1, 2, 3} {
    v := v // shadow
    s[i] = func() { fmt.Println(v) }
}
// Note: Go 1.22+ fixes this — each iteration gets a new variable

// WRONG: comparing slices with ==
a := []int{1, 2, 3}
b := []int{1, 2, 3}
if a == b { }                     // compile error: slices are not comparable

// CORRECT: use slices.Equal or manual loop
if slices.Equal(a, b) { }        // Go 1.21+
```

## Gotchas
- Slice header: (pointer to array, length, capacity) — 24 bytes on 64-bit
- `append` reallocates when len reaches capacity (typically doubles) — pre-allocate with `make([]T, 0, n)` if size is known
- Sub-slices share backing array — modifying one may affect the other until a `copy` is made
- `cap(s)` tells you how many elements can be appended before reallocation
- `s[:len(s):len(s)]` (three-index slice) limits capacity — prevents `append` from corrupting original
- Maps are reference types — passing a map to a function lets it modify entries
- Map iteration order is intentionally randomized by Go — never rely on it
- `nil` map reads return zero values but writes panic — always initialize with `make`
- `delete(m, key)` is a no-op if key doesn't exist — no error
- `sync.Map` is optimized for two patterns: (1) keys written once read many times, (2) disjoint key sets across goroutines. For general concurrent use, `map + sync.RWMutex` is often simpler.
- `range` over a slice copies the value — use index `s[i]` to modify in place
- `slices` and `maps` packages (Go 1.21+) provide generic helpers: `slices.Sort`, `slices.Equal`, `maps.Keys`, etc.
- Zero value of `[]T` is `nil` — `nil` slices behave like empty slices for `append`, `len`, `range`

## Related
- go/stdlib/goroutines.md
- go/stdlib/interfaces.md
- go/concurrency/patterns.md
