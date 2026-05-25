---
id: "go-web-http-server"
title: "HTTP Server with net/http"
language: "go"
category: "web"
tags: ["go", "http", "server", "handler", "mux", "middleware"]
version: "1.21+"
retrieval_hint: "HTTP server handler ServeMux middleware graceful shutdown"
last_verified: "2026-05-24"
confidence: "high"
---

# HTTP Server with net/http

## When to Use
- Building REST APIs
- Creating web services
- Building microservices
- Serving static files

## Standard Pattern

```go
package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

// Handler function
func handleUsers(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		users := []User{{ID: 1, Name: "Alice"}}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(users)
	case http.MethodPost:
		var user User
		if err := json.NewDecoder(r.Body).Decode(&user); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		w.WriteHeader(http.StatusCreated)
		json.NewEncoder(w).Encode(user)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// Middleware pattern
func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("%s %s %v", r.Method, r.URL.Path, time.Since(start))
	})
}

// JSON response helper
func respondJSON(w http.ResponseWriter, status int, data any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

// Error response helper
func respondError(w http.ResponseWriter, status int, message string) {
	respondJSON(w, status, map[string]string{"error": message})
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /users", handleUsers)
	mux.HandleFunc("POST /users", handleUsers)
	mux.HandleFunc("GET /users/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id") // Go 1.22+
		respondJSON(w, 200, map[string]string{"id": id})
	})

	// Apply middleware
	handler := loggingMiddleware(mux)

	// Graceful shutdown
	server := &http.Server{
		Addr:         ":8080",
		Handler:      handler,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	go func() {
		if err := server.ListenAndServe(); err != http.ErrServerClosed {
			log.Fatalf("Server error: %v", err)
		}
	}()

	// Wait for interrupt
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	server.Shutdown(ctx)
}

type User struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}
```

## Common Mistakes

```go
// WRONG: No timeout on server
server := &http.Server{Addr: ":8080"} // Slowloris attack

// CORRECT: Set timeouts
server := &http.Server{
	Addr:         ":8080",
	ReadTimeout:  10 * time.Second,
	WriteTimeout: 10 * time.Second,
	IdleTimeout:  60 * time.Second,
}

// WRONG: Not reading request body to completion
func handler(w http.ResponseWriter, r *http.Request) {
	var user User
	json.NewDecoder(r.Body).Decode(&user)
	// Body not closed — connection reused with unread data
}

// CORRECT: Close body
func handler(w http.ResponseWriter, r *http.Request) {
	defer r.Body.Close()
	var user User
	if err := json.NewDecoder(r.Body).Decode(&user); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
}

// WRONG: Hardcoded port without graceful shutdown
func main() {
	http.ListenAndServe(":8080", nil) // No graceful shutdown
}

// CORRECT: Graceful shutdown (see Standard Pattern above)

// WRONG: Writing headers after body
func handler(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte("hello"))
	w.WriteHeader(200) // Too late — already sent 200
}

// CORRECT: Set status before writing
func handler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(200)
	w.Write([]byte("hello"))
}
```

## Gotchas
- `http.ListenAndServe` blocks — run in a goroutine if you need to do other work
- Go 1.22+ supports method-based routing: `"GET /users/{id}"` — use `{param}` for path variables
- `r.PathValue("id")` extracts path parameters in Go 1.22+
- `json.NewDecoder(r.Body).Decode()` is more memory-efficient than `json.Unmarshal` for large bodies
- `http.Error()` sets Content-Type to `text/plain` — use `respondJSON` for JSON errors
- Middleware wraps handlers — chain them for cross-cutting concerns (logging, auth, CORS)
- `http.Server.Shutdown()` gracefully stops — waits for active connections to complete
- `http.TimeoutHandler` wraps a handler with a timeout — simpler than per-handler timeouts
- Default mux (`http.HandleFunc`) is global — use `http.NewServeMux()` for isolation

## Related
- go/web/http-client.md
- go/stdlib/error-handling.md
- go/stdlib/context.md
