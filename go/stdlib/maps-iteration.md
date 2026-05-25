---
id: "go-stdlib-maps-iteration"
title: "Map Iteration and Operations"
language: "go"
category: "stdlib"
tags: ["go", "map", "iteration", "range", "delete", "sync.Map", "concurrent", "sort-keys"]
version: "1.21+"
retrieval_hint: "map iteration range random order key existence delete sync.Map concurrent"
last_verified: "2026-05-24"
confidence: "high"
---

# Map Iteration and Operations

## When to Use
- Iterating over all key-value pairs in a map
- Checking if a key exists before accessing it
- Safely deleting entries during or after iteration
- Counting entries or collecting keys/values
- Sorting map output by key
- Concurrent map access from multiple goroutines (sync.Map)
- Complement to `slices-maps.md` — this focuses on iteration patterns and concurrent access

## Standard Pattern

```go
package main

import (
	"fmt"
	"maps"
	"slices"
	"sort"
	"sync"
)

// --- Basic iteration ---

func basicIteration() {
	m := map[string]int{
		"apple":  5,
		"banana": 3,
		"cherry": 8,
	}

	// Key-value iteration (order is random)
	for k, v := range m {
		fmt.Printf("%s: %d\n", k, v)
	}

	// Key-only iteration
	for k := range m {
		fmt.Println(k)
	}

	// Value-only iteration
	for _, v := range m {
		fmt.Println(v)
	}
}

// --- Check key existence ---

func checkExistence(m map[string]int, key string) {
	// Comma-ok idiom
	val, ok := m[key]
	if ok {
		fmt.Printf("%s = %d\n", key, val)
	} else {
		fmt.Printf("%s not found\n", key)
	}

	// Just check existence (ignore value)
	if _, exists := m[key]; exists {
		fmt.Println("key exists")
	}
}

// --- Delete keys ---

func deleteKeys() {
	m := map[string]int{"a": 1, "b": 2, "c": 3, "d": 4}

	// Delete single key (no-op if key doesn't exist)
	delete(m, "b")

	// Delete during iteration (safe in Go)
	for k, v := range m {
		if v%2 == 0 {
			delete(m, k) // safe to delete during range
		}
	}
	fmt.Println(m)

	// Collect keys to delete, then delete after iteration
	m = map[string]int{"a": 1, "b": 2, "c": 3, "d": 4}
	var toDelete []string
	for k, v := range m {
		if v > 2 {
			toDelete = append(toDelete, k)
		}
	}
	for _, k := range toDelete {
		delete(m, k)
	}
	fmt.Println(m)
}

// --- Count entries ---

func countEntries() {
	words := []string{"go", "python", "go", "rust", "go", "python"}
	counts := make(map[string]int, len(words))
	for _, w := range words {
		counts[w]++
	}
	fmt.Println(counts) // map[go:3 python:2 rust:1]

	// Total entries
	fmt.Println(len(counts)) // 3
}

// --- Sorting by key ---

func sortByKey() {
	m := map[string]int{
		"cherry": 8,
		"apple":  5,
		"banana": 3,
	}

	// Collect and sort keys
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	// Iterate in sorted order
	for _, k := range keys {
		fmt.Printf("%s: %d\n", k, m[k])
	}

	// Go 1.21+: use maps.Keys + slices.Sort
	keys = maps.Keys(m)
	slices.Sort(keys)
	for _, k := range keys {
		fmt.Printf("%s: %d\n", k, m[k])
	}
}

// --- Collect values ---

func collectValues() {
	m := map[string]int{"a": 1, "b": 2, "c": 3}

	// Go 1.21+
	vals := maps.Values(m)
	slices.Sort(vals)
	fmt.Println(vals) // [1 2 3]
}

// --- sync.Map for concurrent access ---

func syncMapExample() {
	var sm sync.Map

	// Store
	sm.Store("config", map[string]string{"host": "localhost"})
	sm.Store("counter", 0)

	// Load
	if v, ok := sm.Load("config"); ok {
		cfg := v.(map[string]string)
		fmt.Println(cfg["host"]) // "localhost"
	}

	// LoadOrStore — atomic check-and-set
	actual, loaded := sm.LoadOrStore("new-key", "default")
	fmt.Println(actual, loaded) // "default", false

	actual, loaded = sm.LoadOrStore("new-key", "other")
	fmt.Println(actual, loaded) // "default", true (already existed)

	// CompareAndSwap — atomic update
	sm.Store("counter", 0)
	swapped := sm.CompareAndSwap("counter", 0, 1)
	fmt.Println(swapped) // true

	swapped = sm.CompareAndSwap("counter", 0, 2)
	fmt.Println(swapped) // false (current value is 1, not 0)

	// Range (snapshot — may miss concurrent writes)
	sm.Range(func(key, value any) bool {
		fmt.Printf("%v: %v\n", key, value)
		return true // continue iteration
	})

	// Delete
	sm.Delete("counter")
}

// --- Map + RWMutex (alternative to sync.Map) ---

type SafeMap[K comparable, V any] struct {
	mu sync.RWMutex
	m  map[K]V
}

func NewSafeMap[K comparable, V any](size int) *SafeMap[K, V] {
	return &SafeMap[K, V]{m: make(map[K]V, size)}
}

func (s *SafeMap[K, V]) Get(key K) (V, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	v, ok := s.m[key]
	return v, ok
}

func (s *SafeMap[K, V]) Set(key K, val V) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.m[key] = val
}

func (s *SafeMap[K, V]) Delete(key K) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.m, key)
}

func main() {
	basicIteration()
	checkExistence(map[string]int{"x": 10}, "x")
	deleteKeys()
	countEntries()
	sortByKey()
	collectValues()
	syncMapExample()
}
```

## Common Mistakes

```go
// WRONG: assuming map iteration order is consistent
m := map[string]int{"a": 1, "b": 2, "c": 3}
// Running this twice may produce different orders
for k, v := range m {
    fmt.Println(k, v)
}

// CORRECT: sort keys if order matters
keys := maps.Keys(m)
slices.Sort(keys)
for _, k := range keys {
    fmt.Println(k, m[k])
}

// WRONG: checking existence by zero value
m := map[string]int{"count": 0}
val := m["count"]
if val == 0 {
    // Is this "not found" or "actually zero"? Can't tell!
}

// CORRECT: use comma-ok idiom
val, ok := m["count"]
if !ok {
    fmt.Println("key not found")
} else {
    fmt.Printf("value is %d\n", val) // value is 0
}

// WRONG: writing to a nil map
var m map[string]int
m["key"] = 1 // panic: assignment to entry in nil map

// CORRECT: initialize first
m = make(map[string]int)
m["key"] = 1

// WRONG: using sync.Map for single-goroutine access (overhead)
var sm sync.Map
sm.Store("key", "value") // works but slower than plain map

// CORRECT: plain map for single-goroutine, sync.Map only for concurrent access
m := make(map[string]string)
m["key"] = "value"

// WRONG: type assertion without ok check on sync.Map
var sm sync.Map
sm.Store("count", 42)
v := sm.Load("missing")
n := v.(int) // panic: interface conversion (nil to int)

// CORRECT: check ok before type assertion
if v, ok := sm.Load("count"); ok {
    n := v.(int)
    fmt.Println(n)
}

// WRONG: modifying a map while iterating with a collected keys slice
keys := make([]string, 0, len(m))
for k := range m {
    keys = append(keys, k)
}
for _, k := range keys {
    if m[k] > 2 {
        delete(m, k) // safe, but the keys slice still has the deleted key
        // accessing m[k] after delete returns zero value
    }
}

// CORRECT: delete during range is safe in Go
for k, v := range m {
    if v > 2 {
        delete(m, k) // safe
    }
}
```

## Gotchas
- Map iteration order is intentionally randomized by the Go runtime — it changes between runs and even between iterations of the same program
- `delete(m, key)` is a no-op if the key doesn't exist — no error, no panic
- `len(m)` returns the number of key-value pairs — O(1) operation
- `sync.Map` is optimized for two specific patterns: (1) keys written once then read many times, (2) disjoint key sets across goroutines. For general concurrent access, `map + sync.RWMutex` is often simpler and faster.
- `sync.Map.Range` provides a snapshot — it may miss entries written during iteration
- `sync.Map` stores `any` values — you must type-assert on `Load`, which can panic if the type is wrong
- `maps.Keys(m)` and `maps.Values(m)` (Go 1.21+) return slices in random order — sort them if needed
- `maps.Collect(m)` returns all key-value pairs as a slice of `KeyValue` structs
- A `nil` map returns zero values on read but panics on write — always initialize with `make`
- `sync.Map` never shrinks — deleted entries don't free memory until the map is replaced
- `CompareAndSwap` on `sync.Map` enables lock-free atomic updates — useful for counters and flags

## Related
- go/stdlib/slices-maps.md
- go/stdlib/goroutines.md
- go/stdlib/channels.md
