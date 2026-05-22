---
id: "go-stdlib-interfaces"
title: "Interfaces and Type Assertions"
language: "go"
category: "stdlib"
tags: ["go", "interface", "type-assertion", "type-switch", "composition"]
version: "1.21+"
retrieval_hint: "interface type assertion type switch composition io.Reader"
last_verified: "2026-05-22"
confidence: "high"
---

# Interfaces and Type Assertions

## When to Use
- Defining behavior contracts for types
- Writing generic code that works with multiple types
- Dependency injection and testability
- Implementing polymorphism

## Standard Pattern

```go
package main

import (
	"fmt"
	"io"
	"strings"
)

// Define interface (implicit satisfaction)
type Reader interface {
	Read(p []byte) (n int, err error)
}

type Writer interface {
	Write(p []byte) (n int, err error)
}

// Compose interfaces
type ReadWriter interface {
	Reader
	Writer
}

// Any type with Read(p []byte) (int, error) satisfies Reader
type FileReader struct{ path string }

func (f *FileReader) Read(p []byte) (int, error) {
	// Read from file...
	return 0, nil
}

// Empty interface (any)
func printAnything(v any) {
	fmt.Printf("%v\n", v)
}

// Type assertion
func describe(v any) string {
	switch val := v.(type) {
	case string:
		return fmt.Sprintf("string: %q", val)
	case int:
		return fmt.Sprintf("int: %d", val)
	case []byte:
		return fmt.Sprintf("bytes: %d long", len(val))
	default:
		return fmt.Sprintf("unknown: %T", v)
	}
}

// Interface for dependency injection
type UserStore interface {
	GetByID(id int) (*User, error)
	Create(user *User) error
}

type UserService struct {
	store UserStore
}

func NewUserService(store UserStore) *UserService {
	return &UserService{store: store}
}

func (s *UserService) GetUser(id int) (*User, error) {
	return s.store.GetByID(id)
}

// io.Reader/Writer pattern
func processReader(r io.Reader) error {
	buf := make([]byte, 1024)
	for {
		n, err := r.Read(buf)
		if n > 0 {
			process(buf[:n])
		}
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return err
		}
	}
}

// Works with any io.Reader
processReader(strings.NewReader("hello"))
processReader(file)
processReader(resp.Body)

type User struct{ ID int; Name string }
func process(b []byte) {}
```

## Common Mistakes

```go
// WRONG: Pointer receiver implements interface, value doesn't
type MyType struct{}
func (m *MyType) Read(p []byte) (int, error) { return 0, nil }

var r io.Reader = &MyType{} // OK — pointer satisfies
var r io.Reader = MyType{}  // Compile error — value doesn't

// CORRECT: Be consistent — use pointer receivers for interface implementation

// WRONG: Type assertion without checking
func process(v any) int {
	return v.(int) // Panics if v is not int
}

// CORRECT: Check with comma-ok
func process(v any) (int, bool) {
	i, ok := v.(int)
	return i, ok
}

// WRONG: Large interface (violates ISP)
type DataStore interface {
	GetUser(id int) *User
	CreateUser(u *User) error
	DeleteUser(id int) error
	GetOrder(id int) *Order
	CreateOrder(o *Order) error
	SendEmail(to, subject, body string) error
	LogActivity(action string) error
}

// CORRECT: Small, focused interfaces
type UserStore interface {
	GetUser(id int) *User
	CreateUser(u *User) error
	DeleteUser(id int) error
}

type OrderStore interface {
	GetOrder(id int) *Order
	CreateOrder(o *Order) error
}
```

## Gotchas
- Interfaces are satisfied implicitly — no `implements` keyword needed
- Pointer receivers implement interfaces only for pointers, not values
- `any` is an alias for `interface{}` — use `any` in Go 1.18+
- Type assertion panics without the comma-ok pattern — always check
- Type switch (`v.(type)`) only works inside a `switch` statement
- Nil interface value is not nil — a `*MyType(nil)` assigned to an interface is non-nil
- Interface values are comparable but may panic if the underlying type is not comparable
- Small interfaces are idiomatic Go — `io.Reader` has just one method
- Interface composition builds larger interfaces from smaller ones
- Empty interface (`any`) accepts all types but loses type safety

## Related
- go/stdlib/error-handling.md
- go/stdlib/goroutines.md
- go/testing/mocking.md
