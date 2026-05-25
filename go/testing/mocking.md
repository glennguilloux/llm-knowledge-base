---
id: "go-testing-mocking"
title: "Mocking and Test Doubles"
language: "go"
category: "testing"
tags: ["go", "mock", "httptest", "interface", "test-double", "dependency-injection"]
version: "1.21+"
retrieval_hint: "mock interface httptest dependency injection test double fake stub"
last_verified: "2026-05-24"
confidence: "high"
---

# Mocking and Test Doubles

## When to Use
- Testing code that depends on external services (database, HTTP APIs)
- Isolating units under test from their dependencies
- Testing error conditions that are hard to reproduce with real dependencies
- Verifying that specific methods are called with expected arguments

## Standard Pattern

```go
package user

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

// === Interface-based mocking (preferred in Go) ===

// Define a small interface for the dependency
type UserStore interface {
	GetByID(id int) (*User, error)
	Create(user *User) error
}

// Production implementation
type PostgresStore struct{ /* db connection */ }

func (s *PostgresStore) GetByID(id int) (*User, error) { /* real query */ return nil, nil }
func (s *PostgresStore) Create(user *User) error       { /* real insert */ return nil }

// Test double — returns controlled data
type MockStore struct {
	Users     map[int]*User
	CreateErr error
}

func NewMockStore() *MockStore {
	return &MockStore{Users: make(map[int]*User)}
}

func (m *MockStore) GetByID(id int) (*User, error) {
	user, ok := m.Users[id]
	if !ok {
		return nil, fmt.Errorf("user %d not found", id)
	}
	return user, nil
}

func (m *MockStore) Create(user *User) error {
	if m.CreateErr != nil {
		return m.CreateErr
	}
	m.Users[user.ID] = user
	return nil
}

// Service under test — depends on interface, not concrete type
type Service struct {
	store UserStore
}

func NewService(store UserStore) *Service {
	return &Service{store: store}
}

func (s *Service) GetUser(id int) (*User, error) {
	return s.store.GetByID(id)
}

func (s *Service) Register(name, email string) (*User, error) {
	user := &User{Name: name, Email: email}
	if err := s.store.Create(user); err != nil {
		return nil, fmt.Errorf("register: %w", err)
	}
	return user, nil
}

// Test using mock
func TestService_GetUser(t *testing.T) {
	mock := NewMockStore()
	mock.Users[1] = &User{ID: 1, Name: "Alice", Email: "alice@example.com"}
	svc := NewService(mock)

	user, err := svc.GetUser(1)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if user.Name != "Alice" {
		t.Errorf("got name %q, want Alice", user.Name)
	}
}

func TestService_Register_Error(t *testing.T) {
	mock := NewMockStore()
	mock.CreateErr = fmt.Errorf("duplicate email")
	svc := NewService(mock)

	_, err := svc.Register("Bob", "bob@example.com")
	if err == nil {
		t.Fatal("expected error, got nil")
	}
}

// === httptest for HTTP handlers ===

func TestUserHandler(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, `{"id":1,"name":"Alice"}`)
	})

	req := httptest.NewRequest(http.MethodGet, "/users/1", nil)
	w := httptest.NewRecorder()

	handler.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("got status %d, want %d", w.Code, http.StatusOK)
	}

	body := w.Body.String()
	expected := `{"id":1,"name":"Alice"}`
	if body != expected {
		t.Errorf("got body %q, want %q", body, expected)
	}
}

// httptest server for client tests
func TestFetchUser(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprint(w, `{"id":1,"name":"Alice"}`)
	}))
	defer server.Close()

	// Point the client at the test server
	user, err := fetchUser(server.Client(), server.URL+"/users/1")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if user.Name != "Alice" {
		t.Errorf("got %q, want Alice", user.Name)
	}
}

// === Fake — simplified working implementation ===

type FakeStore struct {
	users map[int]*User
	counter int
}

func NewFakeStore() *FakeStore {
	return &FakeStore{users: make(map[int]*User)}
}

func (f *FakeStore) GetByID(id int) (*User, error) {
	u, ok := f.users[id]
	if !ok {
		return nil, fmt.Errorf("not found")
	}
	return u, nil
}

func (f *FakeStore) Create(user *User) error {
	f.counter++
	user.ID = f.counter
	f.users[user.ID] = user
	return nil
}

// Stubs
type User struct{ ID int; Name string; Email string }
func fetchUser(client *http.Client, url string) (*User, error) { return &User{ID:1, Name:"Alice"}, nil }
```

## Common Mistakes

```go
// WRONG: depending on concrete type instead of interface
type Service struct {
    store *PostgresStore   // hard to mock
}

// CORRECT: depend on interface
type Service struct {
    store UserStore         // easy to mock, any implementation works
}

// WRONG: mock too many methods — brittle tests
type MockEverything interface {
    GetUser(id int) (*User, error)
    GetOrder(id int) (*Order, error)
    SendEmail(to string) error
    LogAction(action string) error
}
// Only GetUser is actually used — the rest is noise

// CORRECT: interface segregation — small interfaces
type UserGetter interface {
    GetUser(id int) (*User, error)
}
// Mock only what you need

// WRONG: asserting mock calls but not behavior
mock.AssertCalled(t, "GetByID", 1)  // was it called? yes. did it work? who knows

// CORRECT: verify the outcome through return values
user, err := svc.GetUser(1)
if err != nil { t.Fatalf("unexpected error: %v", err) }
if user.Name != "Alice" { t.Errorf("wrong name") }

// WRONG: test depends on internal implementation details
mock.On("GetByID").Once().Return(...)  // fragile — breaks on refactor

// CORRECT: test through public behavior
user, err := svc.GetUser(1)          // stable — doesn't care how

// WRONG: using global variables for test doubles
var mockDB MockStore   // shared state between tests

// CORRECT: create fresh test double per test
func TestSomething(t *testing.T) {
    mock := NewMockStore()  // isolated
}
```

## Gotchas
- Go doesn't need a mocking framework — interfaces and simple structs work well
- Small interfaces (`UserGetter`, `UserCreator`) are idiomatic and easy to mock
- `httptest.NewServer` creates a real HTTP server for integration tests — `httptest.NewRecorder` tests handlers in-process
- `httptest.NewRecorder` captures response code, headers, and body without network I/O
- Fakes (simplified working implementations) are often better than mocks — they test real behavior
- Mocks verify interactions ("was this called?"), fakes verify state ("is the result correct?")
- Don't mock what you don't own — wrap external dependencies in your own interface
- `t.Cleanup` is useful for shutting down test servers: `t.Cleanup(server.Close)`
- Table-driven tests with different mock configurations cover many scenarios cleanly
- Race detector (`go test -race`) catches shared mock state issues

## Related
- go/testing/testing.md
- go/stdlib/interfaces.md
- go/web/http-server.md
