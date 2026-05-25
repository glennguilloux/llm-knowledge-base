---
id: "patterns-webhook-patterns"
title: "Webhook Patterns: Receiving, Verifying, Retrying"
language: "multi"
category: "patterns"
subcategory: "api-design"
tags: ["webhook", "event", "signature", "retry", "idempotent", "async"]
version: ""
retrieval_hint: "Webhook signature verification retry idempotent event HMAC"
last_verified: "2026-05-24"
confidence: "high"
---

# Webhook Patterns: Receiving, Verifying, Retrying

## When to Use
- Receiving real-time notifications from third-party services (Stripe, GitHub, Twilio)
- Building event-driven architectures between services
- Implementing reliable async communication with idempotency
- Processing events that don't need immediate response

## Standard Pattern

```python
# --- Receiving and verifying webhooks ---
import hmac
import hashlib
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()
WEBHOOK_SECRET = "whsec_..."

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature."""
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

@app.post("/webhooks/stripe")
async def handle_stripe_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature", "")

    if not verify_signature(payload, signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = json.loads(payload)

    # Process idempotently
    if await is_event_processed(event["id"]):
        return {"status": "already_processed"}

    if event["type"] == "payment_intent.succeeded":
        await handle_payment_success(event["data"]["object"])
    elif event["type"] == "payment_intent.failed":
        await handle_payment_failure(event["data"]["object"])

    await mark_event_processed(event["id"])
    return {"status": "ok"}
```

```typescript
// --- Sending webhooks with retries ---
import crypto from "crypto";

function signPayload(payload: string, secret: string): string {
  const signature = crypto.createHmac("sha256", secret).update(payload).digest("hex");
  return `sha256=${signature}`;
}

async function deliverWebhook(url: string, event: WebhookEvent, secret: string) {
  const payload = JSON.stringify(event);
  const signature = signPayload(payload, secret);

  const maxRetries = 5;
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Webhook-Signature": signature,
          "X-Webhook-ID": event.id,
        },
        body: payload,
        signal: AbortSignal.timeout(10000),
      });

      if (response.ok) return;
      if (response.status < 500) return; // Don't retry client errors
    } catch (err) {
      // Network error — retry
    }

    // Exponential backoff: 1s, 2s, 4s, 8s, 16s
    await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 1000));
  }
}
```

## Common Mistakes

```text
# WRONG: Processing webhooks synchronously (may timeout)
POST /webhooks → process event → respond
# If processing takes 30s, webhook provider may retry

# CORRECT: Accept immediately, process async
POST /webhooks → validate → enqueue → respond 200
# Background worker processes the event

# WRONG: Not verifying signatures
@app.post("/webhooks")
async def handler(request: Request):
    event = await request.json()  # Anyone can send fake events!

# CORRECT: Always verify HMAC signature
signature = request.headers.get("X-Webhook-Signature")
if not verify_signature(payload, signature, SECRET):
    raise HTTPException(401)

# WRONG: Not handling duplicates
# Webhook provider may send same event multiple times

# CORRECT: Idempotent processing
if await is_event_processed(event["id"]):
    return {"status": "duplicate"}
```

## Gotchas
- Always verify webhook signatures — never trust the payload blindly
- Respond with 2xx quickly (< 5s) — process asynchronously
- Implement idempotency using event IDs (providers often retry)
- Use exponential backoff for retries (1s, 2s, 4s, 8s, 16s)
- Log all webhook events for debugging (store raw payload)
- Use a dead letter queue for events that fail after all retries
- Provide a webhook testing endpoint that echoes events
- Document your retry policy and expected response codes

## Related
- patterns/rate-limiting.md
- api-design/versioning.md
- patterns/health-checks.md
