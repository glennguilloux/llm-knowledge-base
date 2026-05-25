---
id: "go-stdlib-security-basics"
title: "Go Security Basics: Input Validation, SQL Injection, Hashing, TLS, Rate Limiting"
language: "go"
category: "stdlib"
tags: ["security", "input-validation", "sql-injection", "bcrypt", "tls", "rate-limiting", "crypto"]
version: "1.21+"
retrieval_hint: "Go security input validation SQL injection bcrypt password hashing TLS rate limiting"
last_verified: "2026-05-24"
confidence: "high"
---

# Go Security Basics

## When to Use
- Building HTTP handlers that accept user input
- Storing passwords or sensitive credentials
- Connecting to databases with dynamic queries
- Exposing HTTPS endpoints
- Protecting APIs from abuse and brute-force attacks

## Standard Pattern

```go
package main

import (
    "context"
    "crypto/tls"
    "database/sql"
    "errors"
    "fmt"
    "net"
    "net/http"
    "regexp"
    "strings"
    "sync"
    "time"

    "golang.org/x/crypto/bcrypt"
    _ "github.com/mattn/go-sqlite3"
)

// --- Input Validation ---

var emailRegex = regexp.MustCompile(`^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$`)

type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("%s: %s", e.Field, e.Message)
}

func validateEmail(email string) error {
    email = strings.TrimSpace(email)
    if email == "" {
        return &ValidationError{Field: "email", Message: "cannot be empty"}
    }
    if len(email) > 254 {
        return &ValidationError{Field: "email", Message: "exceeds maximum length of 254"}
    }
    if !emailRegex.MatchString(email) {
        return &ValidationError{Field: "email", Message: "invalid format"}
    }
    return nil
}

func validateUsername(username string) error {
    username = strings.TrimSpace(username)
    if len(username) < 3 || len(username) > 32 {
        return &ValidationError{Field: "username", Message: "must be 3-32 characters"}
    }
    matched, _ := regexp.MatchString(`^[a-zA-Z0-9_]+$`, username)
    if !matched {
        return &ValidationError{Field: "username", Message: "only alphanumeric and underscore allowed"}
    }
    return nil
}

// --- SQL Injection Prevention ---

type UserStore struct {
    db *sql.DB
}

func NewUserStore(db *sql.DB) *UserStore {
    return &UserStore{db: db}
}

// ALWAYS use parameterized queries — never string concatenation
func (s *UserStore) GetUserByEmail(ctx context.Context, email string) (*User, error) {
    var user User
    err := s.db.QueryRowContext(ctx,
        "SELECT id, email, username FROM users WHERE email = ?",
        email,  // Parameterized — safe from SQL injection
    ).Scan(&user.ID, &user.Email, &user.Username)

    if errors.Is(err, sql.ErrNoRows) {
        return nil, nil
    }
    if err != nil {
        return nil, fmt.Errorf("get user by email: %w", err)
    }
    return &user, nil
}

func (s *UserStore) CreateUser(ctx context.Context, email, username string) (int64, error) {
    result, err := s.db.ExecContext(ctx,
        "INSERT INTO users (email, username) VALUES (?, ?)",
        email, username,
    )
    if err != nil {
        return 0, fmt.Errorf("create user: %w", err)
    }
    return result.LastInsertId()
}

// --- Password Hashing with bcrypt ---

func hashPassword(password string) (string, error) {
    // bcrypt.DefaultCost is 10 — good balance of security and performance
    bytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
    if err != nil {
        return "", fmt.Errorf("hash password: %w", err)
    }
    return string(bytes), nil
}

func checkPassword(password, hash string) bool {
    err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
    return err == nil
}

// --- TLS Configuration ---

func newTLSConfig(certFile, keyFile string) (*tls.Config, error) {
    cert, err := tls.LoadX509KeyPair(certFile, keyFile)
    if err != nil {
        return nil, fmt.Errorf("load TLS cert: %w", err)
    }

    return &tls.Config{
        Certificates: []tls.Certificate{cert},
        MinVersion:   tls.VersionTLS12,  // Reject TLS 1.0 and 1.1
        CipherSuites: []uint16{
            tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
            tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
            tls.TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305,
            tls.TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305,
        },
        PreferServerCipherSuites: true,
    }, nil
}

func startTLSServer(handler http.Handler, addr, certFile, keyFile string) error {
    tlsConfig, err := newTLSConfig(certFile, keyFile)
    if err != nil {
        return err
    }

    server := &http.Server{
        Addr:              addr,
        Handler:           handler,
        TLSConfig:         tlsConfig,
        ReadHeaderTimeout: 5 * time.Second,
        ReadTimeout:       10 * time.Second,
        WriteTimeout:      10 * time.Second,
        IdleTimeout:       120 * time.Second,
    }

    return server.ListenAndServeTLS("", "") // certs from TLSConfig
}

// --- Rate Limiting (Token Bucket per IP) ---

type visitor struct {
    tokens    int
    lastSeen  time.Time
    mu        sync.Mutex
}

type RateLimiter struct {
    maxTokens int
    refillRate time.Duration
    visitors  map[string]*visitor
    mu        sync.RWMutex
    cleanupInterval time.Duration
}

func NewRateLimiter(maxTokens int, refillRate time.Duration) *RateLimiter {
    rl := &RateLimiter{
        maxTokens:       maxTokens,
        refillRate:      refillRate,
        visitors:        make(map[string]*visitor),
        cleanupInterval: 5 * time.Minute,
    }
    go rl.cleanup()
    return rl
}

func (rl *RateLimiter) Allow(key string) bool {
    rl.mu.Lock()
    v, exists := rl.visitors[key]
    if !exists {
        v = &visitor{tokens: rl.maxTokens, lastSeen: time.Now()}
        rl.visitors[key] = v
        rl.mu.Unlock()
        return true
    }
    rl.mu.Unlock()

    v.mu.Lock()
    defer v.mu.Unlock()

    // Refill tokens based on elapsed time
    elapsed := time.Since(v.lastSeen)
    newTokens := int(elapsed / rl.refillRate)
    if newTokens > 0 {
        v.tokens = min(v.tokens+newTokens, rl.maxTokens)
        v.lastSeen = time.Now()
    }

    if v.tokens > 0 {
        v.tokens--
        return true
    }
    return false
}

func (rl *RateLimiter) cleanup() {
    ticker := time.NewTicker(rl.cleanupInterval)
    for range ticker.C {
        rl.mu.Lock()
        for key, v := range rl.visitors {
            if time.Since(v.lastSeen) > rl.cleanupInterval*2 {
                delete(rl.visitors, key)
            }
        }
        rl.mu.Unlock()
    }
}

func rateLimitMiddleware(rl *RateLimiter) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            ip, _, _ := net.SplitHostPort(r.RemoteAddr)
            if !rl.Allow(ip) {
                w.Header().Set("Retry-After", "60")
                w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%d", rl.maxTokens))
                http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
                return
            }
            next.ServeHTTP(w, r)
        })
    }
}

// --- Types ---

type User struct {
    ID       int64
    Email    string
    Username string
}

func min(a, b int) int {
    if a < b {
        return a
    }
    return b
}
```

## Common Mistakes

```go
// WRONG: String concatenation in SQL queries
query := "SELECT * FROM users WHERE email = '" + email + "'"
// Attacker inputs: ' OR '1'='1' --  → returns all users

// CORRECT: Parameterized queries
query := "SELECT * FROM users WHERE email = ?"
row := db.QueryRow(query, email)

// WRONG: Storing passwords in plaintext
_, err := db.Exec("INSERT INTO users (email, password) VALUES (?, ?)", email, password)

// CORRECT: Hash passwords with bcrypt before storing
hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
_, err = db.Exec("INSERT INTO users (email, password_hash) VALUES (?, ?)", email, hash)

// WRONG: Using weak TLS settings
&tls.Config{
    MinVersion: tls.VersionTLS10, // TLS 1.0 is deprecated and insecure
}

// CORRECT: Enforce TLS 1.2 minimum
&tls.Config{
    MinVersion: tls.VersionTLS12,
}

// WRONG: No input length limits
func createUser(email string) error {
    // email could be 1MB of garbage
    _, err := db.Exec("INSERT INTO users (email) VALUES (?)", email)
}

// CORRECT: Validate length before processing
func createUser(email string) error {
    if len(email) > 254 {
        return &ValidationError{Field: "email", Message: "too long"}
    }
    // ... proceed
}

// WRONG: Using blacklist for input validation
if !strings.Contains(email, "<script>") {  // Easily bypassed: <Script>, <scr<script>ipt>
    // "safe"
}

// CORRECT: Use whitelist validation
if !emailRegex.MatchString(email) {
    return &ValidationError{Field: "email", Message: "invalid format"}
}

// WRONG: Rate limiter without cleanup — memory leak
rl := NewRateLimiter(100, time.Second)
// visitors map grows forever as new IPs connect

// CORRECT: Periodic cleanup of stale entries (see Standard Pattern above)
```

## Gotchas
- bcrypt has a 72-byte input limit — passwords longer than 72 bytes are silently truncated; pre-hash with SHA-256 if you need longer inputs
- `sql.DB` connections are pooled — parameterized queries are safe because the driver handles escaping, not because of string replacement
- `tls.VersionTLS12` is the minimum; prefer `tls.VersionTLS13` if all clients support it
- Rate limiting by IP can affect users behind NAT (corporate networks, mobile carriers) — consider per-user limits for authenticated endpoints
- `bcrypt.DefaultCost` (10) takes ~100ms on modern hardware; increase to 12-14 for higher security, but benchmark first
- Input validation should happen at the handler boundary, not deep in business logic
- `regexp.Compile` is expensive — compile patterns once at package level, not inside request handlers
- The `database/sql` package prevents injection for VALUES and WHERE clauses, but NOT for table/column names — use whitelists for dynamic identifiers

## Related
- go/stdlib/error-handling.md
- go/stdlib/slog-logging.md
- patterns/rate-limiting.md
- patterns/input-validation.md
