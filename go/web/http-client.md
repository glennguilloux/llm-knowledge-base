---
id: "go-web-http-client"
title: "HTTP Client Patterns"
language: "go"
category: "web"
tags: ["go", "http", "client", "timeout", "retry", "transport", "connection-pool"]
version: "1.21+"
retrieval_hint: "http.Client timeout transport retry request response connection pool"
last_verified: "2026-05-24"
confidence: "high"
---

# HTTP Client Patterns

## When to Use
- Calling REST APIs from Go services
- Building HTTP-based microservice clients
- Downloading files or streaming responses
- Implementing retry and circuit-breaker logic
- Fine-tuning connection pooling and timeouts

## Standard Pattern

```go
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"time"
)

// Production-ready client with timeouts and connection pooling
func newHTTPClient() *http.Client {
	transport := &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 10,
		MaxConnsPerHost:     100,
		IdleConnTimeout:     90 * time.Second,
		DialContext: (&net.Dialer{
			Timeout:   5 * time.Second,
			KeepAlive: 30 * time.Second,
		}).DialContext,
		TLSHandshakeTimeout: 5 * time.Second,
	}

	return &http.Client{
		Timeout:   30 * time.Second,
		Transport: transport,
	}
}

// GET with context and error handling
type User struct {
	ID    int    `json:"id"`
	Name  string `json:"name"`
	Email string `json:"email"`
}

func getUser(ctx context.Context, client *http.Client, userID int) (*User, error) {
	url := fmt.Sprintf("https://api.example.com/users/%d", userID)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Accept", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("do request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("unexpected status %d: %s", resp.StatusCode, body)
	}

	var user User
	if err := json.NewDecoder(resp.Body).Decode(&user); err != nil {
		return nil, fmt.Errorf("decode response: %w", err)
	}
	return &user, nil
}

// POST with JSON body
func createUser(ctx context.Context, client *http.Client, user User) (*User, error) {
	body, err := json.Marshal(user)
	if err != nil {
		return nil, fmt.Errorf("marshal body: %w", err)
	}

	req, err := http.NewRequestWithContext(
		ctx, http.MethodPost,
		"https://api.example.com/users",
		bytes.NewReader(body),
	)
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("do request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("unexpected status %d: %s", resp.StatusCode, body)
	}

	var created User
	if err := json.NewDecoder(resp.Body).Decode(&created); err != nil {
		return nil, fmt.Errorf("decode response: %w", err)
	}
	return &created, nil
}

// Simple retry with exponential backoff
func doWithRetry(ctx context.Context, client *http.Client, req *http.Request, maxRetries int) (*http.Response, error) {
	var resp *http.Response
	var err error

	for attempt := 0; attempt <= maxRetries; attempt++ {
		resp, err = client.Do(req)
		if err == nil && resp.StatusCode < 500 {
			return resp, nil
		}
		if resp != nil {
			resp.Body.Close()
		}

		if attempt < maxRetries {
			backoff := time.Duration(1<<uint(attempt)) * 100 * time.Millisecond
			select {
			case <-ctx.Done():
				return nil, ctx.Err()
			case <-time.After(backoff):
			}
		}
	}
	return nil, fmt.Errorf("after %d retries: %w", maxRetries, err)
}

func main() {
	client := newHTTPClient()
	ctx := context.Background()

	user, err := getUser(ctx, client, 42)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}
	fmt.Printf("User: %+v\n", user)
}
```

## Common Mistakes

```go
// WRONG: default client has no timeout
client := &http.Client{}             // Timeout=0 means no timeout — can hang forever
resp, err := client.Get(url)

// CORRECT: always set a timeout
client := &http.Client{Timeout: 10 * time.Second}

// WRONG: not reading and closing response body
resp, err := http.Get(url)
// Body not closed — connection leaked, eventually pool exhausted

// CORRECT: defer resp.Body.Close() immediately after nil-error check
resp, err := http.Get(url)
if err != nil { return err }
defer resp.Body.Close()

// WRONG: using http.Get/Post (uses default client with no timeout)
resp, err := http.Get("https://api.example.com")  // default client, no timeout

// CORRECT: use custom client
client := newHTTPClient()
resp, err := client.Get("https://api.example.com")

// WRONG: ignoring context cancellation
func fetchData() (*Data, error) {
    resp, err := http.Get(url)  // no context — can't cancel
    // ...
}

// CORRECT: use NewRequestWithContext
func fetchData(ctx context.Context) (*Data, error) {
    req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
    if err != nil { return nil, err }
    resp, err := client.Do(req)
    // ...

// WRONG: reading entire response into memory
body, _ := io.ReadAll(resp.Body)   // dangerous for large responses

// CORRECT: stream or limit
limited := io.LimitReader(resp.Body, 10<<20) // 10MB cap
body, _ := io.ReadAll(limited)

// WRONG: creating a new client per request
for _, url := range urls {
    client := &http.Client{Timeout: 10 * time.Second}  // new transport each time
    client.Get(url)
}

// CORRECT: reuse one client (connection pooling)
client := newHTTPClient()
for _, url := range urls {
    client.Get(url)
}
```

## Gotchas
- `http.Client{Timeout: 0}` means NO timeout — the request can hang forever. Always set a timeout.
- `http.DefaultClient` has no timeout — never use it in production code.
- `http.Get`, `http.Post`, `http.PostForm` use the default client — prefer custom client.
- `resp.Body` must be fully read and closed before the connection can be reused by the pool. Even if you don't need the body, `io.Copy(io.Discard, resp.Body)` before closing.
- `http.Client.Timeout` covers the entire request lifecycle (dial, TLS, headers, body read). For granular control, set timeouts on the `Transport` dialer.
- `MaxIdleConnsPerHost` defaults to 2 — increase for services making many requests to the same host.
- `context.WithTimeout` on the request is independent from `http.Client.Timeout` — whichever fires first cancels the request.
- HTTP 3xx redirects are followed automatically — set `CheckRedirect` to customize or disable.
- Request body can only be read once — for retries, buffer the body with `bytes.NewReader`.
- `json.NewDecoder(resp.Body).Decode` is more memory-efficient than `io.ReadAll` + `json.Unmarshal` for large responses.

## Related
- go/web/http-server.md
- go/stdlib/context.md
- go/stdlib/error-handling.md
