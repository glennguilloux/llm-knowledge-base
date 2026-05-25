---
id: "go-stdlib-structs-methods"
title: "Structs and Methods"
language: "go"
category: "stdlib"
tags: ["go", "struct", "method", "pointer-receiver", "embedding", "composition", "tag", "json"]
version: "1.21+"
retrieval_hint: "struct definition method receiver pointer embedding composition struct tags json db"
last_verified: "2026-05-24"
confidence: "high"
---

# Structs and Methods

## When to Use
- Grouping related data fields into a single type (structs)
- Attaching behavior to data via methods
- Building data models for JSON APIs, database records, or configuration
- Using embedding for composition (Go has no inheritance)
- Adding metadata to fields with struct tags (json, db, validate, etc.)

## Standard Pattern

```go
package main

import (
	"encoding/json"
	"fmt"
)

// Struct definition with JSON and DB tags
type User struct {
	ID        int    `json:"id" db:"id"`
	Name      string `json:"name" db:"name"`
	Email     string `json:"email" db:"email"`
	CreatedAt string `json:"created_at" db:"created_at"`
}

// Value receiver — does not modify the original
func (u User) DisplayName() string {
	return fmt.Sprintf("%s (%s)", u.Name, u.Email)
}

// Pointer receiver — modifies the original struct
func (u *User) SetEmail(newEmail string) {
	u.Email = newEmail
}

// Constructor function (Go convention: New + type name)
func NewUser(id int, name, email string) *User {
	return &User{
		ID:      id,
		Name:    name,
		Email:   email,
	}
}

// Embedding for composition
type Address struct {
	Street string `json:"street"`
	City   string `json:"city"`
}

type Employee struct {
	User              // embedded — promotes fields and methods
	Department string `json:"department"`
	Address    // embedded — promotes fields and methods
}

func main() {
	// Create via constructor
	u := NewUser(1, "Alice", "alice@example.com")

	// Value receiver — original unchanged
	fmt.Println(u.DisplayName()) // Alice (alice@example.com)

	// Pointer receiver — original modified
	u.SetEmail("alice@new.com")
	fmt.Println(u.Email) // alice@new.com

	// Embedding — promoted fields and methods
	e := Employee{
		User:       *u,
		Department: "Engineering",
		Address:    Address{Street: "123 Main St", City: "Springfield"},
	}
	fmt.Println(e.Name)       // Alice — promoted from User
	fmt.Println(e.DisplayName()) // Alice (alice@new.com) — promoted method
	fmt.Println(e.City)       // Springfield — promoted from Address

	// JSON serialization with tags
	data, err := json.Marshal(e)
	if err != nil {
		panic(err)
	}
	fmt.Println(string(data))
	// {"id":1,"name":"Alice","email":"alice@new.com","department":"Engineering","street":"123 Main St","city":"Springfield"}
}
```

## Common Mistakes

```go
// WRONG: using value receiver when modification is needed
type Counter struct{ Count int }

func (c Counter) Increment() {
	c.Count++ // modifies a copy, original unchanged
}

c := Counter{}
c.Increment()
fmt.Println(c.Count) // 0 — not incremented!

// CORRECT: use pointer receiver to modify
func (c *Counter) Increment() {
	c.Count++ // modifies the original
}

c = Counter{}
c.Increment()
fmt.Println(c.Count) // 1

// WRONG: trying to use inheritance (Go has no inheritance)
// type Base struct { Name string }
// type Derived struct { Base } // this is embedding, NOT inheritance
// You cannot pass Derived where Base is expected in function signatures

// CORRECT: use interfaces for polymorphism
type Namer interface {
	GetName() string
}

func PrintName(n Namer) {
	fmt.Println(n.GetName())
}

// WRONG: forgetting that embedding is not a type hierarchy
type Animal struct{ Name string }
func (a Animal) Speak() string { return "..." }

type Dog struct{ Animal } // Dog IS-NOT an Animal

// This does NOT work:
// func Feed(a Animal) { ... }
// Feed(Dog{}) // compile error: cannot use Dog as Animal

// CORRECT: use the embedded value directly or interfaces
func Feed(a Animal) { fmt.Println("feeding", a.Name) }
d := Dog{Animal: Animal{Name: "Rex"}}
Feed(d.Animal) // pass the embedded Animal value

// WRONG: JSON field names controlled by Go export rules, not field name
type Bad struct {
	name string // unexported — json.Marshal skips it entirely
}

// CORRECT: export fields you want in JSON, use tags to control names
type Good struct {
	Name string `json:"name"` // exported + tag controls JSON key
}

// WRONG: nil pointer receiver method call panics
var u *User
u.SetEmail("x@y.com") // panic: nil pointer dereference

// CORRECT: check for nil or ensure initialization
u = &User{}
u.SetEmail("x@y.com") // safe

// WRONG: ambiguous selectors with multiple embedded fields
type A struct{ X int }
type B struct{ X int }
type C struct {
	A
	B
}
var c C
// c.X = 1 // compile error: ambiguous selector c.X

// CORRECT: be explicit
c.A.X = 1
c.B.X = 2
```

## Gotchas
- Method sets: `*T` has all methods of `T` AND `*T`, but `T` only has value-receiver methods. This matters when satisfying interfaces — a `*User` value satisfies an interface requiring pointer-receiver methods, but a `User` value does not.
- Embedding promotes fields and methods, but the embedded type is NOT a subtype. You cannot pass an `Employee` where `User` is expected in function signatures — only the promoted fields/methods are accessible.
- Struct tags are plain strings at compile time — they have no type safety. Typos in tags (e.g., `json:"nmae"`) compile fine but produce wrong output.
- `encoding/json` only serializes exported (capitalized) fields. Unexported fields are silently skipped.
- Zero value of a struct has all fields set to their zero values — no constructor is called automatically.
- When embedding, the promoted method set includes methods from the embedded type. If both the outer and inner type define a method with the same name, the outer one wins (shadowing).
- Struct comparison with `==` works only if all fields are comparable. Structs containing slices, maps, or functions are not comparable.
- `json.Marshal` returns `[]byte` and `error` — always check the error. A nil struct pointer marshals to `"null"`, not an error.

## Related
- go/stdlib/interfaces.md
- go/stdlib/json-custom.md
- go/stdlib/slices-maps.md
