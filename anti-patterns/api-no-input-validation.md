---
id: "anti-patterns-api-no-input-validation"
title: "API Anti-Pattern: Missing Input Validation"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "api", "validation", "schema", "sanitization"]
version: "n/a"
retrieval_hint: "no input validation trusting client data arbitrary JSON Pydantic zod Joi schema validation"
last_verified: "2026-05-24"
confidence: "high"
---

# API Anti-Pattern: Missing Input Validation

## When to Use
- API endpoint design and security reviews
- Building APIs that accept user-provided data
- Preventing injection attacks and data corruption
- Ensuring data integrity at API boundaries

## Standard Pattern

```python
# WRONG: Trusting client data blindly — no validation
@app.post("/users")
async def create_user(request: Request):
    body = await request.json()
    user = await db.create_user(
        name=body["name"],         # KeyError if missing
        email=body["email"],       # Could be anything: "not-an-email", 123, null
        age=body["age"],           # Could be -5 or 999999
        role=body.get("role"),     # Attacker sets role="admin"!
    )
    return user

# CORRECT: Pydantic schema validation at the boundary
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(..., ge=0, le=150)
    role: str = Field(default="user", pattern="^(user|moderator)$")

@app.post("/users", status_code=201)
async def create_user(data: UserCreate):
    user = await db.create_user(**data.model_dump())
    return user
```

```javascript
// WRONG: No validation, accepting arbitrary JSON
app.post("/api/orders", async (req, res) => {
    const { items, total, discount } = req.body;
    // Attacker sends: { "items": [...], "total": 0.01, "discount": 0.99 }
    const order = await db.create({ items, total, discount });
    res.json(order);
});

// CORRECT: Zod schema validation
const { z } = require("zod");

const OrderSchema = z.object({
    items: z.array(z.object({
        productId: z.string().uuid(),
        quantity: z.number().int().positive().max(100),
    })).nonempty(),
    couponCode: z.string().optional(),
});

app.post("/api/orders", async (req, res) => {
    const result = OrderSchema.safeParse(req.body);
    if (!result.success) {
        return res.status(400).json({
            error: "Validation failed",
            details: result.error.issues,
        });
    }
    // total calculated server-side, not from client
    const total = await calculateTotal(result.data.items, result.data.couponCode);
    const order = await db.create({ ...result.data, total });
    res.json(order);
});
```

```java
// WRONG: Accepting raw request body without validation
@PostMapping("/api/orders")
public Order createOrder(@RequestBody Map<String, Object> body) {
    Order order = new Order();
    order.setTotal((Double) body.get("total"));  // ClassCastException, NPE, or price manipulation
    order.setDiscount((Double) body.get("discount"));  // Attacker: discount=1.0 (100% off!)
    return orderRepository.save(order);
}

// CORRECT: Bean Validation with DTOs
public record CreateOrderRequest(
    @NotEmpty List<OrderItem> items,
    @Size(max = 50) String couponCode
) {
    public record OrderItem(
        @NotNull Long productId,
        @Positive @Max(100) Integer quantity
    ) {}
}

@PostMapping("/api/orders")
public ResponseEntity<Order> createOrder(
        @Valid @RequestBody CreateOrderRequest request) {
    BigDecimal total = pricingService.calculateTotal(request.items(), request.couponCode());
    Order order = orderService.create(request.items(), total);
    return ResponseEntity.status(201).body(order);
}
```

## Common Mistakes
The most dangerous validation anti-pattern is trusting client-supplied financial values (prices, totals, discounts) — attackers manipulate these to get free products. Accepting arbitrary JSON without a schema allows unexpected fields to pollute the database or trigger mass assignment vulnerabilities. Missing type validation causes runtime errors (ClassCastException, TypeError) when clients send strings instead of numbers or arrays instead of objects. Validating only on the client side (JavaScript form validation) provides no security — all validation must happen server-side. Forgetting to validate Content-Type headers lets attackers submit form data to JSON endpoints. Not setting maximum payload size allows denial-of-service through memory exhaustion.

## Gotchas
- Validate at the API boundary — don't let unvalidated data reach business logic or database queries
- Server-side validation is security; client-side validation is UX — you need both
- Never trust `total`, `price`, or `discount` from the client — calculate these server-side
- Use `422 Unprocessable Entity` for validation errors (semantically invalid), not `400` (syntactically invalid)
- Validate Content-Type to prevent CSRF-style attacks on JSON endpoints
- Set `max_body_size` to prevent DoS (e.g., Express: `express.json({ limit: '1mb' })`)
- Sanitize strings for HTML to prevent stored XSS, even in API-first apps
- Reject unknown fields (`zod` rejects by default, Pydantic v2 rejects with `model_config = {"extra": "forbid"}`)
- Validate array length to prevent processing thousands of items in a single request
- Use allowlists (whitelists) for enum fields, not denylists (blacklists)

## Related
- security/web-security-basics.md
- anti-patterns/security-antipatterns.md
- anti-patterns/security-mass-assignment.md
- patterns/input-validation.md
