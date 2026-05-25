---
id: "anti-patterns-api-ignoring-idempotency"
title: "API Anti-Pattern: Ignoring Idempotency"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "api", "idempotency", "retry", "duplicate"]
version: "n/a"
retrieval_hint: "idempotency POST duplicate processing retry idempotency key payment double charge"
last_verified: "2026-05-24"
confidence: "high"
---

# API Anti-Pattern: Ignoring Idempotency

## When to Use
- Designing payment and financial transaction APIs
- Building APIs that clients will retry on network failures
- Implementing webhook receivers that may receive duplicate events
- Preventing double-booking, double-charging, or duplicate resource creation

## Standard Pattern

```python
# WRONG: POST creates duplicate on retry — double charge!
@app.post("/payments")
async def create_payment(data: PaymentCreate):
    payment = await db.create_payment(
        user_id=data.user_id,
        amount=data.amount,
    )
    await charge_stripe(data.amount, data.token)
    return payment  # Client retries → double charge!

# CORRECT: Idempotency key prevents duplicates
@app.post("/payments")
async def create_payment(data: PaymentCreate, request: Request):
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        raise HTTPException(400, "Idempotency-Key header required")

    existing = await db.find_payment_by_idempotency_key(idempotency_key)
    if existing:
        return existing  # Return original, no duplicate charge

    payment = await db.create_payment(
        user_id=data.user_id,
        amount=data.amount,
        idempotency_key=idempotency_key,
    )
    await charge_stripe(data.amount, data.token)
    return payment
```

```javascript
// WRONG: POST used for order placement — retried = duplicate orders
app.post("/api/orders", async (req, res) => {
    const order = await db.createOrder({
        userId: req.user.id,
        items: req.body.items,
        total: req.body.total
    });
    await inventory.reserve(req.body.items);
    await payment.charge(req.user.id, req.body.total);
    res.status(201).json(order);  // Retry → 2 orders, 2 charges!
});

// CORRECT: Idempotent order creation with key + request deduplication
app.post("/api/orders", async (req, res) => {
    const idempotencyKey = req.headers["idempotency-key"];
    if (!idempotencyKey) {
        return res.status(400).json({ error: "Idempotency-Key header required" });
    }

    // Check if we already processed this request
    const cached = await redis.get(`idempotent:${idempotencyKey}`);
    if (cached) {
        return res.status(200).json(JSON.parse(cached));
    }

    const order = await db.createOrder({
        userId: req.user.id,
        items: req.body.items,
        total: req.body.total,
        idempotencyKey
    });
    await inventory.reserve(req.body.items);
    await payment.charge(req.user.id, req.body.total);

    // Cache response for 24 hours
    await redis.setex(`idempotent:${idempotencyKey}`, 86400, JSON.stringify(order));
    res.status(201).json(order);
});
```

```java
// WRONG: No idempotency on transfer endpoint — money duplicated on retry
@PostMapping("/transfers")
public Transfer createTransfer(@RequestBody TransferRequest req) {
    accountService.debit(req.getFromAccount(), req.getAmount());
    accountService.credit(req.getToAccount(), req.getAmount());
    return transferService.create(req);  // Client timeout → retry → double transfer
}

// CORRECT: Database-level idempotency with unique constraint
@PostMapping("/transfers")
public ResponseEntity<Transfer> createTransfer(
        @RequestBody TransferRequest req,
        @RequestHeader("Idempotency-Key") String idempotencyKey) {

    // Try to claim this idempotency key
    Optional<Transfer> existing = transferService.findByIdempotencyKey(idempotencyKey);
    if (existing.isPresent()) {
        return ResponseEntity.ok(existing.get());
    }

    try {
        Transfer transfer = transferService.createWithIdempotency(req, idempotencyKey);
        accountService.debit(req.getFromAccount(), req.getAmount());
        accountService.credit(req.getToAccount(), req.getAmount());
        return ResponseEntity.status(201).body(transfer);
    } catch (DuplicateKeyException e) {
        // Race condition: another request claimed the key
        return ResponseEntity.ok(transferService.findByIdempotencyKey(idempotencyKey).orElseThrow());
    }
}
```

## Common Mistakes
The most dangerous idempotency anti-pattern is using POST for operations that create financial consequences without an idempotency key. Network timeouts and automatic retries cause clients to resubmit, resulting in duplicate charges, duplicate orders, or duplicate resource creation. Developers often implement idempotency only for the happy path but forget error states — if a payment partially succeeds (charged but order not created), a retry should complete the order, not charge again. Storing idempotency keys in memory instead of a database loses them on restart. Using a simple "already processed" boolean without atomic check-and-set creates race conditions under concurrent requests.

## Gotchas
- PUT and DELETE are naturally idempotent — POST and PATCH are not
- Idempotency keys should be generated by the client, not the server
- Store idempotency keys with a TTL (24-48 hours) to prevent unbounded storage growth
- Use database unique constraints as a safety net — don't rely solely on application-level checks
- The idempotency key lookup and the business operation must be in the same transaction to prevent race conditions
- Return the original response (including status code) when replaying an idempotent request
- Webhook endpoints should also be idempotent — delivery services (Stripe, Twilio) retry on failure
- Consider using `If-None-Match: *` headers for conditional creates (alternative to idempotency keys)
- Event sourcing naturally provides idempotency through aggregate IDs and event sequencing

## Related
- patterns/rate-limiting.md
- api-design/rest-conventions.md
- anti-patterns/api-incorrect-status-codes.md
