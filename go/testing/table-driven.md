---
id: "go-testing-table-driven"
title: "Go Table-Driven Tests and httptest"
language: "go"
category: "testing"
subcategory: "unit-testing"
tags: ["go", "testing", "table-driven", "httptest", "assert", "testify"]
version: "1.21+"
retrieval_hint: "Go testing table-driven httptest testify assertions HTTP handler test"
last_verified: "2026-05-24"
confidence: "high"
---

# Go Table-Driven Tests and httptest

## When to Use
- Testing functions with multiple input/output combinations
- Testing HTTP handlers without starting a real server
- Testing edge cases systematically
- Using testify for readable assertions

## Standard Pattern

```go
package main

import (
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "strings"
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

// --- Table-driven test ---
func TestCalculate(t *testing.T) {
    tests := []struct {
        name     string
        input    float64
        rate     float64
        want     float64
        wantErr  bool
    }{
        {"positive", 100, 0.1, 110, false},
        {"zero", 0, 0.1, 0, false},
        {"negative rate", 100, -0.1, 0, true},
        {"large value", 1000000, 0.05, 1050000, false},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := Calculate(tt.input, tt.rate)
            if tt.wantErr {
                assert.Error(t, err)
                return
            }
            require.NoError(t, err)
            assert.InDelta(t, tt.want, got, 0.01)
        })
    }
}

// --- HTTP handler test ---
func TestGetUserHandler(t *testing.T) {
    repo := &mockUserRepo{
        users: map[int64]*User{
            1: {ID: 1, Name: "Alice", Email: "alice@test.com"},
        },
    }
    handler := NewUserHandler(repo)

    tests := []struct {
        name       string
        method     string
        path       string
        wantStatus int
        wantName   string
    }{
        {"found", "GET", "/users/1", 200, "Alice"},
        {"not found", "GET", "/users/99", 404, ""},
        {"invalid id", "GET", "/users/abc", 400, ""},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            req := httptest.NewRequest(tt.method, tt.path, nil)
            w := httptest.NewRecorder()

            handler.ServeHTTP(w, req)

            assert.Equal(t, tt.wantStatus, w.Code)
            if tt.wantName != "" {
                var resp User
                require.NoError(t, json.NewDecoder(w.Body).Decode(&resp))
                assert.Equal(t, tt.wantName, resp.Name)
            }
        })
    }
}

// --- POST handler test ---
func TestCreateUserHandler(t *testing.T) {
    handler := NewUserHandler(&mockUserRepo{})

    body := `{"name":"Bob","email":"bob@test.com"}`
    req := httptest.NewRequest("POST", "/users", strings.NewReader(body))
    req.Header.Set("Content-Type", "application/json")
    w := httptest.NewRecorder()

    handler.ServeHTTP(w, req)

    assert.Equal(t, 201, w.Code)

    var resp User
    require.NoError(t, json.NewDecoder(w.Body).Decode(&resp))
    assert.Equal(t, "Bob", resp.Name)
    assert.Equal(t, "bob@test.com", resp.Email)
}

// --- Testify assertions ---
func TestAssertions(t *testing.T) {
    // Equality
    assert.Equal(t, expected, actual)
    assert.NotEqual(t, a, b)

    // Boolean
    assert.True(t, condition)
    assert.False(t, condition)
    assert.Nil(t, value)
    assert.NotNil(t, value)

    // Collections
    assert.Contains(t, "hello world", "world")
    assert.Len(t, items, 3)
    assert.Empty(t, slice)
    assert.NotEmpty(t, slice)

    // Error
    assert.NoError(t, err)
    assert.Error(t, err)
    assert.ErrorIs(t, err, ErrNotFound)

    // require stops test on failure (vs assert which continues)
    require.NoError(t, err)  // Test stops here if err != nil
}
```

## Common Mistakes

```go
// WRONG: Not using t.Run() for subtests
func TestSomething(t *testing.T) {
    for _, tt := range tests {
        got := process(tt.input)  // Can't tell which case failed!
        if got != tt.want {
            t.Errorf("got %v, want %v", got, tt.want)
        }
    }
}

// CORRECT: Use t.Run() for named subtests
func TestSomething(t *testing.T) {
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := process(tt.input)
            assert.Equal(t, tt.want, got)
        })
    }
}

// WRONG: Table test with closure capture issue
for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
        go func() {
            doSomething(tt.input)  // tt may be overwritten in next iteration!
        }()
    })
}

// CORRECT: Capture loop variable
for _, tt := range tests {
    tt := tt  // Capture for goroutine
    t.Run(tt.name, func(t *testing.T) {
        go func() { doSomething(tt.input) }()
    })
}

// WRONG: Using t.Fatal() in goroutine
go func() {
    t.Fatal("failed")  // t.Fatal can't be called from goroutine!
}()

// CORRECT: Use channels or sync to report from goroutines
```

## Gotchas
- `t.Run()` creates a subtest — runs in its own goroutine, can be run with `-run` flag
- `testify/assert` continues on failure; `testify/require` stops the test
- `httptest.NewRequest()` creates a request without network — fast and isolated
- `httptest.NewRecorder()` captures the response for assertion
- Use `t.Parallel()` for tests that don't share state — enables parallel execution
- `t.Cleanup()` runs after the test — use for resource cleanup
- `testify/assert` doesn't stop execution — use `require` for preconditions
- Run specific tests: `go test -run TestGetUser/found`

## Related
- go/testing/testing.md
- go/testing/mocking.md
- go/web/http-server.md
