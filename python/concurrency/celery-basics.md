---
id: "python-concurrency-celery-basics"
title: "Celery Task Queue Basics"
language: "python"
category: "concurrency"
subcategory: "task-queue"
tags: ["celery", "task", "queue", "async", "worker", "redis", "rabbitmq"]
version: "3.10+"
retrieval_hint: "Celery task queue async worker background Redis RabbitMQ retry"
last_verified: "2026-05-22"
confidence: "high"
---

# Celery Task Queue Basics

## When to Use
- Long-running tasks that shouldn't block HTTP responses (PDF generation, video encoding)
- Scheduled/recurring tasks (daily reports, cleanup jobs)
- Reliable task execution with retries, error handling, and monitoring
- Distributed processing across multiple workers/machines

## Standard Pattern

```python
# --- celery_app.py: Configuration ---
from celery import Celery
from celery.schedules import crontab

app = Celery(
    "myapp",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,              # Acknowledge after completion (safer)
    worker_prefetch_multiplier=1,     # One task at a time per worker
    task_soft_time_limit=300,         # 5 min soft limit (raises SoftTimeLimitExceeded)
    task_time_limit=360,              # 6 min hard limit (kills worker task)
    beat_schedule={
        "cleanup-expired-sessions": {
            "task": "tasks.cleanup_sessions",
            "schedule": crontab(hour=3, minute=0),  # 3 AM daily
        },
    },
)


# --- tasks.py: Task definitions ---
from celery_app import app
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(self, to: str, subject: str, body: str) -> dict:
    """Send email with automatic retry on failure."""
    try:
        # smtp.send_message(msg)
        logger.info(f"Email sent to {to}")
        return {"status": "sent", "to": to}
    except ConnectionError as exc:
        logger.warning(f"Email failed, retrying: {exc}")
        raise self.retry(exc=exc)


@app.task(bind=True, soft_time_limit=120)
def generate_report(self, report_id: int) -> dict:
    """Long-running report generation with progress tracking."""
    try:
        self.update_state(state="PROGRESS", meta={"current": 0, "total": 100})
        # ... generate report ...
        self.update_state(state="PROGRESS", meta={"current": 50, "total": 100})
        # ... more work ...
        return {"status": "complete", "report_id": report_id}
    except Exception as exc:
        logger.exception(f"Report {report_id} failed")
        raise


@shared_task
def cleanup_sessions() -> int:
    """Periodic cleanup task."""
    # Delete expired sessions from DB
    deleted = 42  # db.query(Session).filter(Session.expires_at < now).delete()
    return deleted


# --- Calling tasks ---
from tasks import send_email, generate_report

# Async call (returns AsyncResult immediately)
result = send_email.delay("user@example.com", "Welcome!", "Hello!")
print(result.id)  # Task ID for tracking

# Call with countdown (delay execution)
send_email.apply_async(args=["user@example.com", "Reminder", "Don't forget!"], countdown=3600)

# Check result
from celery.result import AsyncResult
task_result = AsyncResult(result.id, app=app)
print(task_result.status)  # PENDING, STARTED, SUCCESS, FAILURE, RETRY
print(task_result.get(timeout=30))  # Block until done
```

## Common Mistakes

```python
# WRONG: Passing database connections to tasks
@app.task
def process_user(db: Session, user_id: int):  # Can't serialize DB connections!
    user = db.query(User).get(user_id)

# CORRECT: Create connections inside the task
@app.task
def process_user(user_id: int):
    with SessionLocal() as db:
        user = db.query(User).get(user_id)

# WRONG: Using .get() inside another task (deadlock risk)
@app.task
def parent_task():
    result = child_task.apply_async(args=[1]).get()  # Blocks worker!

# CORRECT: Use callbacks or chains for task orchestration
from celery import chain
chain(parent_step.s(), child_step.s()).apply_async()

# WRONG: No error handling (task fails silently)
@app.task
def risky_operation():
    external_api_call()  # If this fails, no retry, no logging

# CORRECT: Bind task for self.retry, handle errors explicitly
@app.task(bind=True, max_retries=3)
def risky_operation(self):
    try:
        external_api_call()
    except ConnectionError as exc:
        raise self.retry(exc=exc, countdown=60)
```

## Gotchas
- `bind=True` makes `self` the task instance — needed for `self.retry()` and `self.update_state()`
- `delay()` is shorthand for `apply_async()` — use `apply_async()` for more options (countdown, eta, queue)
- `task_acks_late=True` means tasks survive worker crashes but may be executed twice
- `SoftTimeLimitExceeded` is raised at the soft limit — catch it for cleanup before hard kill
- Use `celery -A celery_app worker --loglevel=info` to start workers
- Use `celery -A celery_app beat` for periodic tasks (separate process)
- Results expire by default (24h) — configure `result_expires` for longer retention
- Use `@shared_task` for reusable tasks that don't depend on a specific app instance

## Related
- python/web/fastapi/background-tasks.md
- python/db/redis/patterns.md
- python/web/fastapi/basics.md
