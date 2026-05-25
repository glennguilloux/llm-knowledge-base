---
id: "go-stdlib-slices-manipulation"
title: "Slice Manipulation"
language: "go"
category: "stdlib"
tags: ["go", "slice", "append", "copy", "delete", "insert", "dedup", "filter", "in-place"]
version: "1.21+"
retrieval_hint: "slice manipulation append copy delete insert deduplicate filter in-place"
last_verified: "2026-05-24"
confidence: "high"
---

# Slice Manipulation

## When to Use
- Adding or removing elements from slices
- Deduplicating or filtering data without extra allocations
- Inserting elements at arbitrary positions
- Copying slices safely (breaking shared backing arrays)
- Complement to `slices-maps.md` — this focuses on mutation operations

## Standard Pattern

```go
package main

import (
	"fmt"
	"slices"
)

// --- Append (basic) ---

func appendExample() {
	s := []int{1, 2, 3}
	s = append(s, 4)          // append single element
	s = append(s, 5, 6, 7)    // append multiple
	s = append(s, []int{8, 9}...) // append another slice (spread)
	fmt.Println(s) // [1 2 3 4 5 6 7 8 9]
}

// --- Copy ---

func copyExample() {
	src := []int{1, 2, 3, 4, 5}
	dst := make([]int, len(src))
	n := copy(dst, src) // n = 5, independent copy
	fmt.Println(n, dst) // 5 [1 2 3 4 5]

	// Copy to shorter slice — truncated
	short := make([]int, 2)
	n = copy(short, src)
	fmt.Println(n, short) // 2 [1 2]

	// Copy to longer slice — zero-padded
	long := make([]int, 8)
	n = copy(long, src)
	fmt.Println(n, long) // 5 [1 2 3 4 5 0 0 0]
}

// --- Delete element (preserves order) ---

func deleteOrdered(s []int, i int) []int {
	if i < 0 || i >= len(s) {
		return s
	}
	return append(s[:i], s[i+1:]...)
}

// --- Delete element (order not preserved — O(1)) ---

func deleteFast(s []int, i int) []int {
	if i < 0 || i >= len(s) {
		return s
	}
	s[i] = s[len(s)-1]
	return s[:len(s)-1]
}

// --- Insert at index ---

func insert(s []int, i int, v int) []int {
	if i < 0 {
		i = 0
	}
	if i > len(s) {
		i = len(s)
	}
	s = append(s, 0)          // grow by 1
	copy(s[i+1:], s[i:])      // shift right
	s[i] = v
	return s
}

// --- Insert multiple values at index ---

func insertAll(s []int, i int, vals ...int) []int {
	if i < 0 {
		i = 0
	}
	if i > len(s) {
		i = len(s)
	}
	s = append(s, make([]int, len(vals))...)
	copy(s[i+len(vals):], s[i:])
	copy(s[i:], vals)
	return s
}

// --- Deduplicate (preserves order, in-place) ---

func dedupOrdered(s []string) []string {
	if len(s) == 0 {
		return s
	}
	seen := make(map[string]struct{}, len(s))
	writeIdx := 0
	for _, v := range s {
		if _, ok := seen[v]; !ok {
			seen[v] = struct{}{}
			s[writeIdx] = v
			writeIdx++
		}
	}
	return s[:writeIdx]
}

// --- Deduplicate sorted slice (no extra memory) ---

func dedupSorted(s []int) []int {
	if len(s) == 0 {
		return s
	}
	writeIdx := 1
	for i := 1; i < len(s); i++ {
		if s[i] != s[i-1] {
			s[writeIdx] = s[i]
			writeIdx++
		}
	}
	return s[:writeIdx]
}

// --- Filter in-place (no allocation) ---

func filterInPlace(s []int, predicate func(int) bool) []int {
	writeIdx := 0
	for _, v := range s {
		if predicate(v) {
			s[writeIdx] = v
			writeIdx++
		}
	}
	return s[:writeIdx]
}

// --- Using slices package (Go 1.21+) ---

func slicesPackageExample() {
	s := []int{1, 2, 3, 4, 5}

	// Delete with slices.Delete
	s = slices.Delete(s, 1, 3) // remove indices [1,3) → [1, 4, 5]

	// Insert with slices.Insert
	s = slices.Insert(s, 1, 10, 20) // insert at index 1 → [1, 10, 20, 4, 5]

	// Clone (independent copy)
	c := slices.Clone(s)

	// Sort
	slices.Sort(s)

	// Compact (dedup sorted)
	sorted := []int{1, 1, 2, 3, 3, 3, 4}
	compacted := slices.Compact(sorted) // [1, 2, 3, 4]

	// Contains
	fmt.Println(slices.Contains(s, 4)) // true

	// Reverse
	slices.Reverse(s)

	_, _, _, _ = c, compacted, sorted, s
}

func main() {
	appendExample()
	copyExample()

	s := []int{1, 2, 3, 4, 5}
	fmt.Println(deleteOrdered(s, 2)) // [1 2 4 5]

	s = []int{1, 2, 3, 4, 5}
	fmt.Println(deleteFast(s, 2)) // [1 2 5 4]

	s = []int{1, 2, 5}
	fmt.Println(insert(s, 2, 3)) // [1 2 3 5]

	words := []string{"a", "b", "a", "c", "b", "d"}
	fmt.Println(dedupOrdered(words)) // [a b c d]

	nums := []int{1, 1, 2, 2, 3, 3, 3}
	fmt.Println(dedupSorted(nums)) // [1 2 3]

	s = []int{1, 2, 3, 4, 5, 6}
	fmt.Println(filterInPlace(s, func(n int) bool { return n%2 == 0 })) // [2 4 6]

	slicesPackageExample()
}
```

## Common Mistakes

```go
// WRONG: delete with append but original slice is modified too
original := []int{1, 2, 3, 4, 5}
sub := original[:4]           // shares backing array
sub = append(sub[:1], sub[2:]...) // deletes from sub
fmt.Println(original)         // [1 3 4 5 5] — corrupted!

// CORRECT: use three-index slice to limit capacity before append
sub = original[:1:1]          // len=1, cap=1
sub = append(sub, original[2:]...) // forces allocation
fmt.Println(original)         // [1 2 3 4 5] — untouched

// WRONG: insert without growing first — overwrites data
s := []int{1, 2, 3}
copy(s[1:], s[0:])            // shift right without growing
s[0] = 99
fmt.Println(s)                // [99 1 1] — lost 2 and 3

// CORRECT: append first to grow, then shift
s = []int{1, 2, 3}
s = append(s, 0)              // grow: [1, 2, 3, 0]
copy(s[1:], s[:3])            // shift: [1, 1, 2, 3]
s[0] = 99                     // insert: [99, 1, 2, 3]

// WRONG: dedup without map — O(n²) and still wrong
func badDedup(s []string) []string {
	result := make([]string, 0)
	for _, v := range s {
		found := false
		for _, r := range result {
			if r == v {
				found = true
				// forgot to break — keeps checking unnecessarily
			}
		}
		if !found {
			result = append(result, v)
		}
	}
	return result
}

// CORRECT: use a map for O(n) dedup
func goodDedup(s []string) []string {
	seen := make(map[string]struct{}, len(s))
	result := make([]string, 0, len(s))
	for _, v := range s {
		if _, ok := seen[v]; !ok {
			seen[v] = struct{}{}
			result = append(result, v)
		}
	}
	return result
}

// WRONG: filter in-place but returning the wrong slice
func badFilter(s []int) []int {
	n := 0
	for _, v := range s {
		if v%2 == 0 {
			s[n] = v
			n++
		}
	}
	return s // returns full slice including garbage at end
}

// CORRECT: truncate the slice
func goodFilter(s []int) []int {
	n := 0
	for _, v := range s {
		if v%2 == 0 {
			s[n] = v
			n++
		}
	}
	return s[:n]
}

// WRONG: using copy with overlapping source and destination incorrectly
s := []int{1, 2, 3, 4, 5}
copy(s[2:], s[1:]) // copies from s[1:5] to s[2:6]
// Result: [1, 2, 2, 2, 2] — not a right-shift!

// CORRECT: use copy in the right direction for right-shift
s = []int{1, 2, 3, 4, 5}
copy(s[3:], s[2:4]) // copy from end to avoid overwrite
// Or simply: copy(s[i+1:], s[i:]) works because copy handles overlap
```

## Gotchas
- `append(s[:i], s[i+1:]...)` modifies the backing array — if any other slice shares it, they see the change. Use `s[:i:i]` (three-index slice) to force a copy before append.
- `copy` handles overlapping source and destination correctly — it copies in the right order to avoid overwriting. But the semantics are "copy min(len(dst), len(src)) elements".
- `slices.Delete(s, i, j)` removes `[i:j)` — the upper bound is exclusive, like Go slice expressions
- `slices.Insert(s, i, vals...)` grows the slice and shifts elements right — O(n) operation
- `slices.Compact` only removes consecutive duplicates — sort first if you need full dedup
- In-place filter with `s[:0]` pattern reuses the backing array — the filtered-out elements remain in memory until the slice is garbage collected
- `slices.Clone` creates a new slice with a new backing array — safe to modify independently
- `slices.Sort` is not stable — use `slices.SortStable` if equal elements must keep their order
- When inserting at index 0, all elements shift right — consider if a prepend-then-reverse or a linked structure would be better for your use case

## Related
- go/stdlib/slices-maps.md
- go/stdlib/goroutines.md
