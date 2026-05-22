---
id: "python-web-fastapi-background-tasks"
title: "FastAPI Background Tasks"
language: "python"
category: "web"
subcategory: "api-framework"
tags: ["fastapi", "background", "tasks", "async", "email", "processing"]
version: "3.10+"
retrieval_hint: "FastAPI background task after response send email processing"
last_verified: "2026-05-22"
confidence: "high"
---

# FastAPI Background Tasks

## When to Use
- Sending emails after form submission without blocking the response
- Logging, analytics, or audit trail writes that don't affect the response
- Cleanup operations (temp files, expired sessions) after request completes
- Triggering webhooks or external API calls asynchronously

## Standard Pattern

```python
from fastapi import FastAPI, BackgroundTasks, Depends
from pydantic import BaseModel
import logging

app = FastAPI()
logger = logging.getLogger(__name__)


class EmailData(BaseModel):
    to: str
    subject: str
    body: str


def send_email_notification(email_data: EmailData) -> None:
    """Runs after response is sent. Exceptions are logged but don't affect client."""
    try:
        # Simulate email sending
        logger.info(f"Sending email to {email_data.to}: {email_data.subject}")
        # smtp.send_message(msg)
    except Exception:
        logger.exception(f"Failed to send email to {email_data.to}")


def log_action(user_id: int, action: str) -> None:
    """Audit logging that runs after response."""
    logger.info(f"User {user_id} performed: {action}")


@app.post("/orders")
async def create_order(
    order: dict,
    background_tasks: BackgroundTasks,
) -> dict:
    # Main logic runs synchronously in the request
    order_id = 123  # save to DB

    # Task runs AFTER response is sent to client
    background_tasks.add_task(
        send_email_notification,
        EmailData(to="user@example.com", subject="Order confirmed", body=f"Order {order_id}"),
    )
    background_tasks.add_task(log_action, user_id=1, action=f"created_order_{order_id}")

    return {"order_id": order_id}


# With dependency injection
async def get_current_user():
    return {"id": 1, "email": "user@example.com"}


@app.post("/subscribe")
async def subscribe(
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
) -> dict:
    background_tasks.add_task(
        send_email_notification,
        EmailData(to=user["email"], subject="Welcome!", body="Thanks for subscribing"),
    )
    return {"status": "subscribed"}
```

## Common Mistakes

```python
# WRONG: Expecting background task exceptions to reach the client
@app.post("/action")
async def do_action(background_tasks: BackgroundTasks):
    background_tasks.add_task(risky_operation)  # If this fails, client never knows
    return {"status": "ok"}

# CORRECT: Handle critical operations in the request, defer only non-critical ones
@app.post("/action")
async def do_action(background_tasks: BackgroundTasks):
    result = critical_db_write()  # Do this BEFORE responding
    background_tasks.add_task(send_notification, result.id)  # Defer non-critical
    return {"status": "ok", "id": result.id}

# WRONG: Using BackgroundTasks for long-running jobs
@app.post("/export")
async def export_data(background_tasks: BackgroundTasks):
    background_tasks.add_task(generate_large_csv)  # Takes 10 minutes, blocks worker

# CORRECT: Use Celery or a task queue for long-running work
@app.post("/export")
async def export_data():
    task = celery_app.send_task("generate_csv", args=[user_id])
    return {"task_id": task.id}

# WRONG: Passing database sessions to background tasks
@app.post("/items")
async def create_item(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    item = Item(name="test")
    db.add(item)
    db.commit()
    background_tasks.add_task(update_search_index, db)  # Session may be closed!

# CORRECT: Create a new session inside the background task
def update_search_index():
    with SessionLocal() as db:
        items = db.query(Item).all()
        # update search index

@app.post("/items")
async def create_item(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    item = Item(name="test")
    db.add(item)
    db.commit()
    background_tasks.add_task(update_search_index)  # Creates own session
```

## Gotchas
- Background tasks run in the same process as the request handler, not in a separate worker
- If the server crashes before tasks complete, those tasks are lost (no persistence)
- Exceptions in background tasks are logged but never sent to the client
- Tasks execute sequentially in the order added, not in parallel
- For long-running or reliable tasks, use Celery, RQ, or Arq instead
- Background tasks share the application's lifespan — they won't outlive the server
- The response is sent BEFORE tasks start executing

## Related
- python/web/fastapi/basics.md
- python/web/fastapi/dependency-injection.md
- python/concurrency/celery-basics.md
