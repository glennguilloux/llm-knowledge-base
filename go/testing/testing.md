---
id: "go-testing-basics"
title: "Testing with testing Package"
language: "go"
category: "testing"
tags: ["go", "testing", "benchmark", "subtest", "table-driven", "TestMain"]
version: "1.21+"
retrieval_hint: "test benchmark subtest table-driven TestMain t.Run t.Helper"
last_verified: "2026-05-22"
confidence: "high"
---

# Testing with testing Package

## When to Use
- Writing unit tests for Go packages
- Running benchmarks to measure performance
- Table-driven testing for multiple input/output combinations
- Setting up shared test fixtures with TestMain
- Using subtests for organized test output

## Standard Pattern

```go
package calculator

import (
	"fmt"
	"math"
	"os"
	"testing"
)

// Basic test
func TestAdd(t *testing.T) {
	result := Add(2, 3)
	if result != 5 {
		t.Errorf("Add(2, 3) = %d, want 5", result)
	}
}

// Helper function — errors show caller's line
func assertEqual(t *testing.T, got, want int) {
	t.Helper()
	if got != want {
		t.Errorf("got %d, want %d", got, want)
	}
}

// Table-driven test
func TestAdd(t *testing.T) {
	tests := []struct {
		name     string
		a, b     int
		expected int
	}{
		{"positive", 2, 3, 5},
		{"zero", 0, 0, 0},
		{"negative", -1, -2, -3},
		{"mixed", -1, 5, 4},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := Add(tt.a, tt.b)
			assertEqual(t, got, tt.expected)
		})
	}
}

// Table-driven with error cases
func TestDivide(t *testing.T) {
	tests := []struct {
		name      string
		a, b      float64
		want      float64
		wantErr   bool
	}{
		{"normal", 10, 2, 5, false},
		{"by_zero", 10, 0, 0, true},
		{"negative", -10, 2, -5, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := Divide(tt.a, tt.b)
			if (err != nil) != tt.wantErr {
				t.Errorf("Divide(%v, %v) error = %v, wantErr %v", tt.a, tt.b, err, tt.wantErr)
				return
			}
			if !tt.wantErr && math.Abs(got-tt.want) > 1e-9 {
				t.Errorf("Divide(%v, %v) = %v, want %v", tt.a, tt.b, got, tt.want)
			}
		})
	}
}

// TestMain — runs once for the package
func TestMain(m *testing.M) {
	// Setup: create test database, seed data, etc.
	setup()

	code := m.Run()

	// Teardown: clean up
	teardown()
	os.Exit(code)
}

// Benchmark
func BenchmarkAdd(b *testing.B) {
	for i := 0; i < b.N; i++ {
		Add(2, 3)
	}
}

func BenchmarkStringConcat(b *testing.B) {
	for i := 0; i < b.N; i++ {
		s := ""
		for j := 0; j < 100; j++ {
			s += "x"
		}
	}
}

func BenchmarkStringBuilder(b *testing.B) {
	for i := 0; i < b.N; i++ {
		var sb strings.Builder
		for j := 0; j < 100; j++ {
			sb.WriteString("x")
		}
		_ = sb.String()
	}
}

// Parallel tests
func TestParallel(t *testing.T) {
	tests := []struct {
		name string
	}{/* ... */}
	for _, tt := range tests {
		tt := tt // capture loop variable (Go <1.22)
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			// test body
		})
	}
}

// Stubs
func setup()    {}
func teardown() {}
func Add(a, b int) int { return a + b }
func Divide(a, b float64) (float64, error) {
	if b == 0 { return 0, fmt.Errorf("division by zero") }
	return a / b, nil
}
```

## Common Mistakes

```go
// WRONG: not using t.Helper in test helpers
func assertNoError(t *testing.T, err error) {
    if err != nil {
        t.Errorf("unexpected error: %v", err) // error shows helper line, not caller
    }
}

// CORRECT: call t.Helper()
func assertNoError(t *testing.T, err error) {
    t.Helper() // now errors show caller's line
    if err != nil {
        t.Errorf("unexpected error: %v", err)
    }
}

// WRONG: not using subtests — failures are hard to identify
func TestCases(t *testing.T) {
    for _, tt := range tests {
        result := Process(tt.input)
        if result != tt.want {
            t.Errorf("got %v, want %v", result, tt.want) // which case failed?
        }
    }
}

// CORRECT: use t.Run for named subtests
func TestCases(t *testing.T) {
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := Process(tt.input)
            if result != tt.want {
                t.Errorf("got %v, want %v", result, tt.want)
            }
        })
    }
}

// WRONG: test relies on global state or specific order
var counter int
func TestIncrement(t *testing.T) {
    counter++
    // another test might have already modified counter
}

// CORRECT: each test is independent
func TestIncrement(t *testing.T) {
    counter := 0
    counter++
    assertEqual(t, counter, 1)
}

// WRONG: using fmt.Println instead of t.Log
func TestSomething(t *testing.T) {
    fmt.Println("debug output") // always prints, clutters output
}

// CORRECT: use t.Log (only shown with -v flag or on failure)
func TestSomething(t *testing.T) {
    t.Log("debug output") // hidden unless verbose
}

// WRONG: calling b.ReportAllocations inside loop
func BenchmarkFoo(b *testing.B) {
    for i := 0; i < b.N; i++ {
        b.ReportAllocs() // called N times, not meaningful
    }
}

// CORRECT: call before loop
func BenchmarkFoo(b *testing.B) {
    b.ReportAllocs()
    for i := 0; i < b.N; i++ {
        Foo()
    }
}
```

## Gotchas
- Test files must end with `_test.go` — only compiled during `go test`
- `go test ./...` runs all tests in the module recursively
- `go test -run TestAdd/positive` runs a specific subtest by name pattern
- `go test -v` shows verbose output including `t.Log` messages
- `go test -count=1` disables test caching — use when debugging
- `go test -race` enables the race detector — catches data races at runtime
- `go test -bench=. -benchmem` runs benchmarks with memory allocation stats
- `b.N` is adjusted by the benchmark runner — never set it yourself
- `b.ResetTimer()` resets the timer after expensive setup inside a benchmark
- `t.Parallel()` marks the test as safe to run concurrently with others
- `TestMain` controls the test binary lifecycle — must call `os.Exit(m.Run())`
- Loop variable capture: before Go 1.22, `tt := tt` is required inside `t.Run` closures
- Table-driven tests are the idiomatic Go pattern — preferred over one function per case
- `t.Cleanup(func)` registers cleanup that runs after the test — like `defer` for tests
- Testdata directory: `go test` ignores it by default — use for golden files and fixtures

## Real-World Example

### Table-Driven HTTP Handler Tests with Subtests and Golden Files

```go
package handlers

import (
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "os"
    "path/filepath"
    "testing"
)

func TestUserHandler(t *testing.T) {
    tests := []struct {
        name       string
        method     string
        path       string
        body       string
        wantStatus int
        wantBody   string // path to golden file, or inline JSON
    }{
        {
            name:       "get user success",
            method:     "GET",
            path:       "/users/1",
            wantStatus: 200,
            wantBody:   "testdata/golden/user_1.json",
        },
        {
            name:       "get user not found",
            method:     "GET",
            path:       "/users/999",
            wantStatus: 404,
            wantBody:   `{"error":"user not found"}`,
        },
        {
            name:       "create user success",
            method:     "POST",
            path:       "/users",
            body:       `{"name":"Alice","email":"alice@example.com"}`,
            wantStatus: 201,
            wantBody:   "testdata/golden/user_created.json",
        },
        {
            name:       "create user invalid json",
            method:     "POST",
            path:       "/users",
            body:       `{invalid`,
            wantStatus: 400,
            wantBody:   `{"error":"invalid JSON"}`,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            req := httptest.NewRequest(tt.method, tt.path, strings.NewReader(tt.body))
            req.Header.Set("Content-Type", "application/json")
            rr := httptest.NewRecorder()

            handler := NewUserHandler(testDB)
            handler.ServeHTTP(rr, req)

            if rr.Code != tt.wantStatus {
                t.Errorf("status = %d, want %d", rr.Code, tt.wantStatus)
            }

            // Compare against golden file or inline expected body
            if _, err := os.Stat(tt.wantBody); err == nil {
                golden, _ := os.ReadFile(tt.wantBody)
                if strings.TrimSpace(rr.Body.String()) != strings.TrimSpace(string(golden)) {
                    t.Errorf("body mismatch:\ngot:  %s\nwant: %s", rr.Body.String(), string(golden))
                }
            } else {
                if strings.TrimSpace(rr.Body.String()) != tt.wantBody {
                    t.Errorf("body = %q, want %q", rr.Body.String(), tt.wantBody)
                }
            }
        })
    }
}
```

## Related
- go/testing/mocking.md
- go/stdlib/error-handling.md
- go/web/http-server.md
