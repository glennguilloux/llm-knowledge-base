---
id: "go-web-http-mux-modern"
title: "Modern Go HTTP Mux (net/http 1.22+ Routing)"
language: "go"
category: "web"
subcategory: "routing"
tags: ["go", "http", "mux", "routing", "go1.22", "nethttp", "middleware", "servehttp"]
version: "1.22+"
retrieval_hint: "Go HTTP mux routing ServeMux path parameters method-based middleware go1.22"
last_verified: "2026-05-25"
confidence: "high"
---

# Modern Go HTTP Mux (net/http 1.22+ Routing)

## When to Use
- New Go HTTP services where you want zero external dependencies
- Replacing gorilla/mux, chi, or httprouter with stdlib-only routing
- Simple to moderate REST APIs that need path parameters and method matching
- Not when you need advanced middleware ecosystems or subdomain routing

## Standard Pattern

```go
package main

import (
	"fmt"
	"log"
	"net/http"
	"time"
)

// --- Method-based routing (Go 1.22+) ---
// Syntax: "METHOD /path/{param}"
func main() {
	mux := http.NewServeMux()

	// Pattern: "GET /api/users" — matches GET only
	// Pattern: "/api/users" — matches any method
	mux.HandleFunc("GET /api/users", listUsers)
	mux.HandleFunc("POST /api/users", createUser)

	// Path parameters with {name}
	mux.HandleFunc("GET /api/users/{id}", getUser)
	mux.HandleFunc("PUT /api/users/{id}", updateUser)
	mux.HandleFunc("DELETE /api/users/{id}", deleteUser)

	// Wildcard suffix with {...}
	mux.HandleFunc("GET /api/users/{id}/posts/{postid}", getUserPost)

	// Exact match vs trailing slash
	mux.HandleFunc("GET /api/health", healthCheck)

	// Fallback — matches any method, any path under /static/
	mux.HandleFunc("GET /static/", serveStatic)

	// --- Middleware ---
	wrappedMux := withMiddleware(mux)

	log.Fatal(http.ListenAndServe(":8080", wrappedMux))
}

// --- Path parameter extraction ---
func getUser(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id") // Returns the {id} value — Go 1.22+
	fmt.Fprintf(w, "Get user: %s", id)
}

func getUserPost(w http.ResponseWriter, r *http.Request) {
	userID := r.PathValue("id")
	postID := r.PathValue("postid")
	fmt.Fprintf(w, "User %s, Post %s", userID, postID)
}

func listUsers(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "List users")
}

func createUser(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Create user")
}

func updateUser(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	fmt.Fprintf(w, "Update user: %s", id)
}

func deleteUser(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	fmt.Fprintf(w, "Delete user: %s", id)
}

func healthCheck(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, `{"status": "ok"}`)
}

func serveStatic(w http.ResponseWriter, r *http.Request) {
	// Note: r.PathValue("*") gives the wildcard match
	http.ServeFile(w, r, "./public/"+r.PathValue("*"))
}

// --- Middleware pattern ---
func withMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Request logging
		log.Printf("%s %s %s", r.Method, r.URL.Path, r.RemoteAddr)

		// CORS headers
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")

		// Handle preflight
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}

		// Wrap ResponseWriter for status code capture
		lrw := &loggingResponseWriter{ResponseWriter: w, statusCode: http.StatusOK}
		next.ServeHTTP(lrw, r)

		log.Printf("Completed %d in %v", lrw.statusCode, time.Since(start))
	})
}

type loggingResponseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (lrw *loggingResponseWriter) WriteHeader(code int) {
	lrw.statusCode = code
	lrw.ResponseWriter.WriteHeader(code)
}
```

## Common Mistakes

```go
// WRONG: Pattern conflict — overlapping patterns cause panic at registration
mux := http.NewServeMux()
mux.HandleFunc("GET /users/{id}", handler)    // Matches /users/123
mux.HandleFunc("GET /users/new", otherHandler)  // Also matches /users/new
// PANIC: pattern "GET /users/new" conflicts with pattern "GET /users/{id}"

// CORRECT: Put more specific patterns first — or avoid overlap
// Go 1.22 mux sees {id} as matching "new" too.
// Solution: use a different path structure:
//   /users/{id} and /users/new/ (with trailing slash) — no conflict
// Or handle the disambiguation in the handler.

// WRONG: Using regex or complex patterns inside {param}
mux.HandleFunc("GET /api/users/{id:[0-9]+}", handler)
// ERROR: pattern syntax doesn't support regex — only bare {name}

// CORRECT: Validate in the handler
mux.HandleFunc("GET /api/users/{id}", func(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	if !isValidUUID(id) {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}
	// ...
})

// WRONG: Forgetting that /api/health matches /api/health TOO with trailing content
// Pattern "GET /api/health" matches ONLY "/api/health"
// Pattern "GET /api/health/" matches "/api/health/" and "/api/health/anything"
// But NOT "/api/health" (without trailing slash)!

// CORRECT: Be explicit about trailing slashes
mux.HandleFunc("GET /api/health", healthHandler)  // exact
mux.HandleFunc("GET /api/health/", healthHandler)  // prefix-based
```

## Gotchas
- **Pattern conflicts cause runtime panics:** The Go 1.22 mux validates patterns at registration time. Two patterns that could match the same request path cause a panic in `HandleFunc`. You cannot register both `/users/new` and `/users/{id}` — the mux sees `new` as a potential `{id}` value.
- **`{param}` matches any non-empty segment:** A parameter `{id}` matches `abc`, `123`, or even `new`. It does NOT match an empty segment. Use `{$}` for exact path end matching if needed.
- **`{$}` is the end-of-path marker:** Older Go used trailing slash `/` to denote prefix matching. Go 1.22+ introduces `{$}` for exact match: `GET /api/health{$}` matches only `/api/health`, not `/api/health/more`.
- **Method validation is strict:** `"GET /api/users"` matches ONLY GET requests. `"POST /api/users"` matches ONLY POST. No method prefix (just `/api/users`) matches ANY method. There's no built-in `OPTIONS` handling — implement it in middleware.
- **Middleware wrapping nuance:** `http.ServeMux` itself implements `http.Handler`. Middleware wraps the mux, not individual routes. For per-route middleware, you need a third-party router or wrap handlers manually.

## Related
- go/web/http-server.md
- go/stdlib/error-handling.md
