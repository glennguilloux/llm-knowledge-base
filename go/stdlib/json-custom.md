---
id: "go-stdlib-json-custom"
title: "Go JSON Custom Marshaling"
language: "go"
category: "stdlib"
subcategory: "serialization"
tags: ["go", "json", "marshal", "unmarshal", "custom", "encoding"]
version: "1.21+"
retrieval_hint: "Go JSON marshal unmarshal custom encoding jsoniter struct tags"
last_verified: "2026-05-22"
confidence: "high"
---

# Go JSON Custom Marshaling

## When to Use
- Custom JSON serialization (different field names, formats)
- Handling nullable fields or empty values
- Parsing non-standard JSON structures
- Controlling which fields are included/excluded dynamically

## Standard Pattern

```go
package main

import (
    "encoding/json"
    "fmt"
    "time"
)

// --- Struct tags ---
type User struct {
    ID        int64     `json:"id"`
    Name      string    `json:"name"`
    Email     string    `json:"email,omitempty"`
    Password  string    `json:"-"`              // Never serialized
    CreatedAt time.Time `json:"created_at"`
    Age       *int      `json:"age,omitempty"`  // Pointer: omits if nil
}

// --- Custom marshaler ---
type CustomTime struct {
    time.Time
}

func (ct CustomTime) MarshalJSON() ([]byte, error) {
    return json.Marshal(ct.Format("2006-01-02"))
}

func (ct *CustomTime) UnmarshalJSON(data []byte) error {
    var s string
    if err := json.Unmarshal(data, &s); err != nil {
        return err
    }
    t, err := time.Parse("2006-01-02", s)
    if err != nil {
        return err
    }
    ct.Time = t
    return nil
}

type Event struct {
    Name string     `json:"name"`
    Date CustomTime `json:"date"`
}

// --- Dynamic field inclusion ---
type UserResponse struct {
    User
    IncludeEmail bool `json:"-"`  // Control flag, not serialized
}

func (u UserResponse) MarshalJSON() ([]byte, error) {
    type resp struct {
        ID   int64  `json:"id"`
        Name string `json:"name"`
    }
    if u.IncludeEmail {
        type withEmail struct {
            ID    int64  `json:"id"`
            Name  string `json:"name"`
            Email string `json:"email"`
        }
        return json.Marshal(withEmail{u.ID, u.Name, u.Email})
    }
    return json.Marshal(resp{u.ID, u.Name})
}

// --- Handling unknown fields ---
type Config struct {
    Known   string          `json:"known"`
    Extra   json.RawMessage `json:"extra,omitempty"`  // Raw JSON for unknown fields
}

// --- JSON lines (JSONL) ---
func ReadJSONL(data []byte) ([]User, error) {
    var users []User
    for _, line := range bytes.Split(data, []byte("\n")) {
        if len(line) == 0 {
            continue
        }
        var user User
        if err := json.Unmarshal(line, &user); err != nil {
            return nil, fmt.Errorf("parse line: %w", err)
        }
        users = append(users, user)
    }
    return users, nil
}
```

## Common Mistakes

```go
// WRONG: Unexported fields are not serialized
type User struct {
    id    int64  `json:"id"`    // lowercase = unexported, ignored!
    name  string `json:"name"`
}

// CORRECT: Export fields (capitalized)
type User struct {
    ID    int64  `json:"id"`
    Name  string `json:"name"`
}

// WRONG: Using omitempty on required fields
type User struct {
    ID   int64  `json:"id,omitempty"`   // ID=0 is omitted!
    Name string `json:"name,omitempty"` // Empty name is omitted
}

// CORRECT: Use omitempty only for truly optional fields
type User struct {
    ID    int64  `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email,omitempty"`  // Optional
}

// WRONG: Not handling errors from json.NewDecoder
json.NewDecoder(r.Body).Decode(&user)  // Error silently ignored

// CORRECT: Always check errors
if err := json.NewDecoder(r.Body).Decode(&user); err != nil {
    http.Error(w, "Invalid JSON", 400)
    return
}

// WRONG: Using json.Marshal for large data (allocates entire buffer)
data, _ := json.Marshal(hugeSlice)  // Memory spike

// CORRECT: Stream with json.NewEncoder
json.NewEncoder(w).Encode(hugeSlice)  // Writes incrementally
```

## Gotchas
- Unexported fields (lowercase) are silently ignored by `encoding/json`
- `omitempty` omits zero values: `0`, `""`, `nil`, `false`, empty slices/maps
- `json:"-"` completely excludes a field from JSON
- Pointer fields (`*int`) with `omitempty` are omitted when nil (useful for nullable)
- `json.RawMessage` defers parsing — useful for polymorphic JSON
- Custom marshalers implement `json.Marshaler` / `json.Unmarshaler` interfaces
- `json.NewDecoder` streams from `io.Reader`; `json.Unmarshal` works on `[]byte`
- `json.Number` type preserves numeric precision (use `Decoder.UseNumber()`)

## Related
- go/web/http-server.md
- go/stdlib/error-handling.md
- go/db/database-sql.md
