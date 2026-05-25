---
id: "go-stdlib-enums"
title: "Enums with iota"
language: "go"
category: "stdlib"
tags: ["go", "enum", "iota", "constant", "stringer", "marshaling", "typed-const"]
version: "1.0+"
retrieval_hint: "enum iota const block string method JSON marshal typed constant"
last_verified: "2026-05-24"
confidence: "high"
---

# Enums with iota

## When to Use
- Defining a fixed set of related constants (status codes, states, modes, roles)
- Need string representation for logging, debugging, or API output
- Need JSON serialization/deserialization of enum values
- Replacing magic numbers or bare strings with type-safe constants

## Standard Pattern

```go
package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

// --- Basic enum with iota ---

type StatusCode int

const (
	StatusPending StatusCode = iota // 0
	StatusActive                    // 1
	StatusPaused                    // 2
	StatusDone                      // 3
	StatusError                     // 4
)

// String method — required for fmt.Println, logging, etc.
func (s StatusCode) String() string {
	switch s {
	case StatusPending:
		return "pending"
	case StatusActive:
		return "active"
	case StatusPaused:
		return "paused"
	case StatusDone:
		return "done"
	case StatusError:
		return "error"
	default:
		return fmt.Sprintf("StatusCode(%d)", s)
	}
}

// --- JSON marshaling ---

// MarshalJSON implements json.Marshaler
func (s StatusCode) MarshalJSON() ([]byte, error) {
	return json.Marshal(s.String())
}

// UnmarshalJSON implements json.Unmarshaler
func (s *StatusCode) UnmarshalJSON(data []byte) {
	var str string
	if err := json.Unmarshal(data, &str); err != nil {
		*s = StatusError
		return
	}
	switch strings.ToLower(str) {
	case "pending":
		*s = StatusPending
	case "active":
		*s = StatusActive
	case "paused":
		*s = StatusPaused
	case "done":
		*s = StatusDone
	case "error":
		*s = StatusError
	default:
		*s = StatusError
	}
}

// --- Validation method ---

func (s StatusCode) IsValid() bool {
	switch s {
	case StatusPending, StatusActive, StatusPaused, StatusDone, StatusError:
		return true
	}
	return false
}

// --- Using the enum ---

type Task struct {
	ID     int        `json:"id"`
	Status StatusCode `json:"status"`
}

func main() {
	task := Task{ID: 1, Status: StatusActive}

	// String representation
	fmt.Println(task.Status) // "active"

	// JSON output
	data, _ := json.Marshal(task)
	fmt.Println(string(data)) // {"id":1,"status":"active"}

	// JSON input
	var task2 Task
	json.Unmarshal([]byte(`{"id":2,"status":"paused"}`), &task2)
	fmt.Println(task2.Status) // "paused"

	// Validation
	fmt.Println(StatusActive.IsValid()) // true
	fmt.Println(StatusCode(99).IsValid()) // false

	// Unknown value string
	fmt.Println(StatusCode(42)) // "StatusCode(42)"
}
```

## Common Mistakes

```go
// WRONG: using bare int instead of typed constant — no type safety
const (
	Pending = iota // int, not a named type
	Active
)

func process(status int) { } // accepts any int, not just enum values

// CORRECT: define a named type
type Status int
const (
	Pending Status = iota
	Active
)
func process(status Status) { } // type-safe

// WRONG: forgetting to handle unknown values in String()
func (s StatusCode) String() string {
	names := []string{"pending", "active", "paused"}
	return names[s] // panics if s >= len(names)
}

// CORRECT: bounds check or switch with default
func (s StatusCode) String() string {
	switch s {
	case StatusPending:
		return "pending"
	case StatusActive:
		return "active"
	case StatusPaused:
		return "paused"
	default:
		return fmt.Sprintf("StatusCode(%d)", s)
	}
}

// WRONG: using iota with gaps and forgetting to account for them
const (
	Red   = iota // 0
	_            // 1 — skipped
	Green        // 2
	Blue         // 3
)
// String() switch must handle the gap or use a slice with care

// CORRECT: either skip explicitly in the switch or use a slice with sentinel
func (c Color) String() string {
	switch c {
	case Red:
		return "red"
	case Green:
		return "green"
	case Blue:
		return "blue"
	default:
		return fmt.Sprintf("Color(%d)", c)
	}
}

// WRONG: UnmarshalJSON on value receiver (can't modify the receiver)
func (s StatusCode) UnmarshalJSON(data []byte) error { // value receiver!
	// ...
	*s = StatusActive // compile error: cannot assign to *s
}

// CORRECT: use pointer receiver
func (s *StatusCode) UnmarshalJSON(data []byte) error {
	// ...
	*s = StatusActive // works
	return nil
}

// WRONG: MarshalJSON returning a bare string without quotes
func (s StatusCode) MarshalJSON() ([]byte, error) {
	return []byte(s.String()), not nil // invalid JSON — needs quotes
}

// CORRECT: use json.Marshal which adds quotes
func (s StatusCode) MarshalJSON() ([]byte, error) {
	return json.Marshal(s.String())
}
```

## Gotchas
- `iota` starts at 0 in each `const` block — use `_ = iota` or a blank identifier to skip 0 if you need 1-based values
- Typed enum constants are not exported unless the type and const are both exported (`type Status int` + `const StatusOk Status = iota`)
- `iota` resets to 0 in every new `const` block — if you need continuous values across blocks, use explicit values
- The `stringer` tool (`golang.org/x/tools/cmd/stringer`) can auto-generate `String()` methods — run `go generate` to keep them in sync
- JSON marshaling of enums is not automatic — you must implement `json.Marshaler` and `json.Unmarshaler` interfaces
- Enum values can be created from any integer via type conversion (`StatusCode(99)`) — always validate with an `IsValid()` method
- `fmt.Stringer` interface (the `String()` method) is used by `fmt.Println`, `log.Printf`, `%v`, `%s` — but NOT by `%+v` on structs unless the field type implements it
- Comparing enum values with `==` is safe and idiomatic — `if status == StatusActive { }`
- Sentinel values: it's common to add `_` or `invalid` as the first iota value (0) to catch uninitialized variables

## Related
- go/stdlib/json-custom.md
- go/stdlib/interfaces.md
