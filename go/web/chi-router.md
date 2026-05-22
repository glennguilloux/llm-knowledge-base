---
id: "go-web-chi-router"
title: "Chi Router for Go HTTP Services"
language: "go"
category: "web"
subcategory: "router"
tags: ["go", "chi", "router", "middleware", "http", "rest", "api"]
version: "1.21+"
retrieval_hint: "Go Chi router middleware REST API routing group handler"
last_verified: "2026-05-22"
confidence: "high"
---

# Chi Router for Go HTTP Services

## When to Use
- Building REST APIs in Go with composable routing
- Middleware chains (auth, logging, CORS)
- Route grouping and versioning (v1, v2)
- Lightweight alternative to Gin/Echo with stdlib compatibility

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
    "time"

    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
)

func NewRouter(repo *UserRepo) *chi.Mux {
    r := chi.NewRouter()

    // Global middleware
    r.Use(middleware.Logger)
    r.Use(middleware.Recoverer)
    r.Use(middleware.RequestID)
    r.Use(middleware.RealIP)
    r.Use(corsMiddleware)

    // Routes
    r.Route("/api/v1", func(r chi.Router) {
        r.Route("/users", func(r chi.Router) {
            r.Get("/", listUsers(repo))
            r.Post("/", createUser(repo))

            r.Route("/{userID}", func(r chi.Router) {
                r.Use(userCtx)  // Middleware for this group
                r.Get("/", getUser(repo))
                r.Put("/", updateUser(repo))
                r.Delete("/", deleteUser(repo))
            })
        })
    })

    // Health check
    r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
        json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
    })

    return r
}

// --- Middleware ---
func corsMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Access-Control-Allow-Origin", "*")
        w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
        if r.Method == "OPTIONS" {
            w.WriteHeader(http.StatusOK)
            return
        }
        next.ServeHTTP(w, r)
    })
}

func userCtx(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        userID := chi.URLParam(r, "userID")
        ctx := context.WithValue(r.Context(), "userID", userID)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// --- Handlers ---
func listUsers(repo *UserRepo) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        users, err := repo.List(r.Context(), 20, 0)
        if err != nil {
            http.Error(w, err.Error(), 500)
            return
        }
        respondJSON(w, 200, users)
    }
}

func getUser(repo *UserRepo) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        userID := r.Context().Value("userID").(string)
        user, err := repo.GetByID(r.Context(), userID)
        if err != nil {
            http.Error(w, "Not found", 404)
            return
        }
        respondJSON(w, 200, user)
    }
}

func respondJSON(w http.ResponseWriter, status int, data any) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(data)
}

// --- Graceful shutdown ---
func main() {
    repo := NewUserRepo(db)
    router := NewRouter(repo)

    srv := &http.Server{
        Addr:         ":8080",
        Handler:      router,
        ReadTimeout:  10 * time.Second,
        WriteTimeout: 10 * time.Second,
        IdleTimeout:  60 * time.Second,
    }

    go func() {
        log.Printf("Server starting on %s", srv.Addr)
        if err := srv.ListenAndServe(); err != http.ErrServerClosed {
            log.Fatalf("Server error: %v", err)
        }
    }()

    // Graceful shutdown
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, os.Interrupt)
    <-quit

    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    srv.Shutdown(ctx)
}
```

## Common Mistakes

```go
// WRONG: Using http.DefaultServeMux (no middleware support)
http.HandleFunc("/api/users", handler)  // No middleware chain

// CORRECT: Use chi.NewRouter() for middleware support
r := chi.NewRouter()
r.Use(middleware.Logger)
r.Get("/api/users", handler)

// WRONG: Not reading URL params correctly
userID := r.URL.Query().Get("userID")  // Query param, not path param!

// CORRECT: Use chi.URLParam() for path parameters
userID := chi.URLParam(r, "userID")

// WRONG: Not setting Content-Type for JSON responses
w.Write(jsonBytes)  // Client may not parse as JSON

// CORRECT: Set Content-Type header
w.Header().Set("Content-Type", "application/json")
w.Write(jsonBytes)

// WRONG: No graceful shutdown (drops in-flight requests)
log.Fatal(http.ListenAndServe(":8080", router))

// CORRECT: Handle OS signals and shutdown gracefully
srv := &http.Server{Addr: ":8080", Handler: router}
go srv.ListenAndServe()
<-quit
srv.Shutdown(ctx)
```

## Gotchas
- `chi.URLParam()` gets path params; `r.URL.Query().Get()` gets query params
- Middleware in `r.Use()` applies to all routes; middleware in `r.Route()` applies to that group
- `{userID}` in path is a wildcard; `/{userID}` captures the value
- `chi.NewRouter()` returns `*chi.Mux` which implements `http.Handler`
- Use `r.Group()` for route groups without new middleware
- `middleware.Recoverer` catches panics and returns 500 — always use it
- `middleware.RequestID` adds a unique ID to each request — useful for tracing
- Chi is compatible with any `http.Handler` middleware (stdlib or third-party)

## Related
- go/web/http-server.md
- go/web/http-client.md
- go/stdlib/error-handling.md
