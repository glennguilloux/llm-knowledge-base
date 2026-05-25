---
id: "anti-patterns-api-incorrect-status-codes"
title: "API Anti-Pattern: Incorrect HTTP Status Codes"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "api", "http", "status-codes", "rest"]
version: "n/a"
retrieval_hint: "incorrect HTTP status codes 200 for errors 500 for validation proper REST status code usage"
last_verified: "2026-05-24"
confidence: "high"
---

# API Anti-Pattern: Incorrect HTTP Status Codes

## When to Use
- Designing REST API response conventions
- Reviewing API error handling code
- Training LLMs to generate correct HTTP responses
- Building API client libraries that branch on status codes

## Standard Pattern

```python
# WRONG: Always returning 200 with error in body
@app.post("/users")
async def create_user(data: UserCreate):
    if not data.email:
        return JSONResponse(status_code=200, content={"error": "Email required"})
    if await user_exists(data.email):
        return JSONResponse(status_code=200, content={"error": "User exists"})
    user = await db.create(data)
    return JSONResponse(status_code=200, content={"user": user, "error": None})

# CORRECT: Proper status codes for each outcome
@app.post("/users", status_code=201)
async def create_user(data: UserCreate):
    if not data.email:
        raise HTTPException(422, detail="Email is required")
    if await user_exists(data.email):
        raise HTTPException(409, detail="User with this email already exists")
    user = await db.create(data)
    return user  # 201 Created
```

```javascript
// WRONG: 500 for validation errors, 200 for not found
app.get("/api/products/:id", async (req, res) => {
    try {
        const product = await db.findById(req.params.id);
        if (!product) {
            return res.status(500).json({ error: "Product not found" });
        }
        res.json(product);
    } catch (err) {
        res.status(200).json({ error: err.message });  // 200 for errors??
    }
});

// CORRECT: Semantic status codes
app.get("/api/products/:id", async (req, res) => {
    if (!isValidId(req.params.id)) {
        return res.status(400).json({ error: "Invalid product ID format" });
    }
    const product = await db.findById(req.params.id);
    if (!product) {
        return res.status(404).json({ error: "Product not found" });
    }
    res.json(product);  // 200 OK (default)
});

app.delete("/api/products/:id", async (req, res) => {
    const deleted = await db.deleteById(req.params.id);
    if (!deleted) {
        return res.status(404).json({ error: "Product not found" });
    }
    res.status(204).send();  // 204 No Content
});
```

```java
// WRONG: Using 201 for GET, 200 for DELETE with body
@GetMapping("/orders")
public ResponseEntity<List<Order>> getOrders() {
    return ResponseEntity.status(201).body(orderService.findAll());  // 201 for GET??
}

@DeleteMapping("/orders/{id}")
public ResponseEntity<Order> deleteOrder(@PathVariable Long id) {
    Order deleted = orderService.delete(id);
    return ResponseEntity.ok(deleted);  // 200 with body for DELETE
}

// CORRECT: Semantic status codes
@GetMapping("/orders")
public ResponseEntity<List<Order>> getOrders() {
    return ResponseEntity.ok(orderService.findAll());  // 200 OK
}

@PostMapping("/orders")
public ResponseEntity<Order> createOrder(@RequestBody Order order) {
    Order created = orderService.create(order);
    URI location = URI.create("/orders/" + created.getId());
    return ResponseEntity.created(location).body(created);  // 201 Created
}

@DeleteMapping("/orders/{id}")
public ResponseEntity<Void> deleteOrder(@PathVariable Long id) {
    orderService.delete(id);
    return ResponseEntity.noContent().build();  // 204 No Content
}
```

## Common Mistakes
The most pervasive anti-pattern is returning `200 OK` for all responses and putting error information in the response body. This forces every client to inspect the body for errors, defeats HTTP caching, and breaks monitoring tools that rely on status codes. Returning `500 Internal Server Error` for validation errors (`422 Unprocessable Entity`) or not-found resources (`404 Not Found`) pollutes error logs and misleads debugging. Using `201 Created` for GET requests violates the HTTP spec. Failing to return `204 No Content` for successful DELETE operations that return no body wastes bandwidth.

## Gotchas
- `200` is the default — only use it when the request succeeded and there's a response body
- `201 Created` must include a `Location` header pointing to the new resource
- `204 No Content` is correct for DELETE and PUT when there's nothing to return
- `400 Bad Request` is for malformed requests (bad JSON, missing required fields)
- `401 Unauthorized` means "not authenticated" (misleading name) — use `403 Forbidden` for "not authorized"
- `404 Not Found` should be used when a specific resource doesn't exist — not for missing endpoints
- `409 Conflict` is for business logic conflicts (duplicate email, concurrent modification)
- `422 Unprocessable Entity` is for validation errors on syntactically correct but semantically invalid data
- `429 Too Many Requests` should include `Retry-After` header
- Don't use `500` for expected error conditions — it signals a bug in your server

## Related
- api-design/error-response-format.md
- api-design/rest-conventions.md
- anti-patterns/api-ignoring-idempotency.md
