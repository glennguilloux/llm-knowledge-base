---
id: "go-stdlib-error-handling"
title: "Error Handling Patterns"
language: "go"
category: "stdlib"
tags: ["go", "error", "errors", "error-handling", "sentinel", "wrap"]
version: "1.21+"
retrieval_hint: "error handling sentinel errors Is As wrap fmt.Errorf"
last_verified: "2026-05-24"
confidence: "high"
---

# Error Handling Patterns

## When to Use
- Handling failures in function calls
- Creating custom error types
- Propagating errors with context
- Checking for specific error types

## Standard Pattern

```go
package main

import (
	"errors"
	"fmt"
	"os"
)

// Sentinel errors (package-level)
var (
	ErrNotFound     = errors.New("not found")
	ErrUnauthorized = errors.New("unauthorized")
	ErrInvalidInput = errors.New("invalid input")
)

// Custom error type
type ValidationError struct {
	Field   string
	Message string
}

func (e *ValidationError) Error() string {
	return fmt.Sprintf("validation error: %s - %s", e.Field, e.Message)
}

// Error wrapping with context
func readConfig(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read config %s: %w", path, err) // Wraps error
	}
	// ...
}

// Checking specific errors
func handleRequest() error {
	err := readConfig("config.yaml")
	if errors.Is(err, os.ErrNotExist) {
		return createDefaultConfig()
	}
	if err != nil {
		return err
	}
}

// Type assertion on errors
func validate(input string) error {
	if input == "" {
		return &ValidationError{Field: "input", Message: "cannot be empty"}
	}
	return nil
}

func process() error {
	err := validate("")
	var ve *ValidationError
	if errors.As(err, &ve) {
		fmt.Printf("Validation failed: field=%s msg=%s\n", ve.Field, ve.Message)
		return nil
	}
	return err
}

// Error handling in main
func main() {
	if err := run(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}

func run() error {
	// Business logic here — all errors propagated to main
	return nil
}
```

## Common Mistakes

```go
// WRONG: Ignoring errors
data, _ := os.ReadFile("config.yaml") // Silent failure

// CORRECT: Always handle errors
data, err := os.ReadFile("config.yaml")
if err != nil {
	return fmt.Errorf("read config: %w", err)
}

// WRONG: Using panic for normal errors
func divide(a, b int) int {
	if b == 0 {
		panic("division by zero") // Not for normal error flow
	}
	return a / b
}

// CORRECT: Return error
func divide(a, b int) (int, error) {
	if b == 0 {
		return 0, errors.New("division by zero")
	}
	return a / b, nil
}

// WRONG: Comparing error strings
if err.Error() == "not found" { // Fragile — breaks on message change

// CORRECT: Compare error values
if errors.Is(err, ErrNotFound) {

// WRONG: Not wrapping errors (loses context)
func read(path string) ([]byte, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err // No context about what was being read
	}
	return data, nil
}

// CORRECT: Wrap with context
func read(path string) ([]byte, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read file %s: %w", path, err)
	}
	return data, nil
}

// WRONG: Checking type without errors.As
if _, ok := err.(*ValidationError); ok { // Doesn't work with wrapped errors

// CORRECT: Use errors.As (works with wrapped errors)
var ve *ValidationError
if errors.As(err, &ve) {
	// Handle validation error
}
```

## Gotchas
- Go errors are values — check them explicitly, don't use try/catch equivalents
- `fmt.Errorf("...: %w", err)` wraps the error — `errors.Is/As` can unwrap it
- `errors.Is` checks if the target error is anywhere in the error chain
- `errors.As` extracts a specific error type from the chain
- `panic` is for truly unrecoverable errors — not normal error flow
- `recover` only works inside deferred functions
- Sentinel errors should be compared with `errors.Is`, not `==`
- Error messages should describe what failed, not just that it failed
- Don't return `error` AND a valid result — return zero value + error
- The `_` blank identifier explicitly ignores a return value — document why

## Related
- go/stdlib/interfaces.md
- go/web/http-server.md
- go/testing/testing.md
