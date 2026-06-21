---
id: "python-web-background-tasks"
title: "Background Task Patterns for Python Web Applications"
language: "python"
category: "web"
subcategory: "async-processing"
tags: ["background-tasks", "fastapi", "flask", "queue", "email", "exports", "retries"]
version: "3.10+"
retrieval_hint: "Python web background tasks FastAPI BackgroundTasks Celery RQ queue durable jobs retries idempotency long-running"
last_verified: "2026-05-24"
confidence: "medium"
---

# Background Task Patterns for Python Web Applications

## When to Use
- Sending notifications after a response is accepted
- Running short cleanup, audit, or cache-warming work that should not block the client
- Offloading long-running exports, reports, or third-party API calls to a durable queue
- Returning a task identifier for polling, webhooks, or progress checks
- Keeping request handlers small while preserving reliability boundaries

## Standard Pattern

```python
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

import logging

from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI()
logger = logging.getLogger(__name__)


class TaskKind(str, Enum):
    WELCOME_EMAIL = "welcome_email"
    PDF_EXPORT = "pdf_export"


@dataclass(frozen=True)
class TaskEnvelope:
    task_id: str
    kind: TaskKind
    payload: dict[str, str | int | bool]


class WelcomePayload(BaseModel):
    user_id: int = Field(gt=0)
    email: str = Field(min_length=3, max_length=254)
    language: str = Field(default="en", min_length=2, max_length=5)


def load_user_for_task(user_id: int) -> dict[str, int | str]:
    # In production, load from the database and raise 404 if missing.
    return {"user_id": user_id, "email": f"user{user_id}@example.test", "language": "en"}


def send_welcome_email(payload: WelcomePayload) -> None:
    """In-process task for short work that may be retried manually if lost."""
    try:
        logger.info("sending welcome email to user_id=%s", payload.user_id)
    except Exception:
        logger.exception("failed to send welcome email for user_id=%s", payload.user_id)


def persist_job_record(kind: TaskKind, payload: dict[str, str | int | bool]) -> str:
    """Persist a job row before publishing so retries can be idempotent."""
    task_id = str(uuid4())
    logger.info("persisted job task_id=%s kind=%s", task_id, kind.value)
    return task_id


def publish_to_queue(task_id: str, kind: TaskKind, payload: dict[str, str | int | bool]) -> None:
    """Publish to Celery, RQ, Arq, or another worker system in production."""
    envelope = TaskEnvelope(task_id=task_id, kind=kind, payload=payload)
    logger.info("published durable job %s", envelope)


def run_pdf_export(task_id: str, invoice_id: int) -> None:
    """Durable worker function; safe to retry with the same task_id."""
    logger.info("running pdf export task_id=%s invoice_id=%s", task_id, invoice_id)


@app.post("/users/{user_id}/welcome")
async def queue_welcome_email(user_id: int, background_tasks: BackgroundTasks) -> dict:
    user = load_user_for_task(user_id)
    payload = WelcomePayload(
        user_id=user["user_id"],
        email=user["email"],
        language=user["language"],
    )
    background_tasks.add_task(send_welcome_email, payload)
    return {"queued": "in-process", "user_id": user_id}


@app.post("/exports/invoices/{invoice_id}")
async def export_invoice(invoice_id: int) -> dict:
    if invoice_id <= 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    payload = {"invoice_id": invoice_id}
    task_id = persist_job_record(TaskKind.PDF_EXPORT, payload)
    publish_to_queue(task_id, TaskKind.PDF_EXPORT, payload)
    return {"task_id": task_id, "queued": "durable", "status": "pending"}
```

## Common Mistakes

```python
# WRONG: Using BackgroundTasks for work that can take minutes
@app.post("/exports")
async def export_all(background_tasks: BackgroundTasks):
    background_tasks.add_task(generate_large_report)
    return {"status": "started"}

# CORRECT: Persist and publish long-running work to a durable queue
@app.post("/exports")
async def export_all():
    task_id = persist_job_record(TaskKind.PDF_EXPORT, {"scope": "all"})
    publish_to_queue(task_id, TaskKind.PDF_EXPORT, {"scope": "all"})
    return {"task_id": task_id, "status": "pending"}
```

```python
# WRONG: Passing request objects or database sessions into background work
background_tasks.add_task(update_search_index, request, db_session)

# CORRECT: Pass small serializable payloads and open resources inside the task
background_tasks.add_task(update_search_index, product_id, serialized_payload)
```

```python
# WRONG: Responding before the critical database transaction commits
background_tasks.add_task(send_receipt, order_id)
return {"status": "created"}  # Task may run even if commit fails

# CORRECT: Save critical writes first, then enqueue only non-critical side effects
order_id = create_order(data)
background_tasks.add_task(send_receipt, order_id)
return {"order_id": order_id}
```

```python
# WRONG: Retrying a side effect without an idempotency key
send_payment_webhook(order_id)

# CORRECT: Store task_id and make the side effect safe to run more than once
send_payment_webhook(task_id=task_id, order_id=order_id)
```

## Gotchas
- FastAPI `BackgroundTasks` run after the response is sent but in the same worker process
- In-process background tasks are lost if the worker crashes before the task finishes
- Tasks added to `BackgroundTasks` run sequentially in the order they were added
- Durable queues need persisted job rows, retries, dead-letter handling, and idempotency keys
- Never pass `Request`, `Session`, file handles, or other per-request resources to background work
- Keep task payloads small; store large blobs in object storage or the database and pass identifiers
- Multi-worker deployments can run in-process background tasks on any worker, so avoid local-only state
- Measure task duration before choosing between `BackgroundTasks`, threads, and a worker queue

## Related
- python/web/fastapi/background-tasks.md
- python/web/fastapi/dependency-injection.md
- python/web/websocket.md
