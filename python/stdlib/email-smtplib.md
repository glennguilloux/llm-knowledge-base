---
id: "python-stdlib-email-smtplib"
title: "Sending Emails with smtplib and email"
language: "python"
category: "stdlib"
subcategory: "networking"
tags: ["email", "smtp", "smtplib", "mime", "send", "attachment"]
version: "3.10+"
retrieval_hint: "email smtplib SMTP send email attachment MIME HTML template"
last_verified: "2026-05-22"
confidence: "high"
---

# Sending Emails with smtplib and email

## When to Use
- Sending notification emails from applications (order confirmations, alerts)
- Sending emails with HTML content and file attachments
- Automated reporting via email (daily digests, error reports)
- Contact form submissions that forward to an inbox

## Standard Pattern

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from dataclasses import dataclass


@dataclass
class EmailConfig:
    host: str
    port: int
    username: str
    password: str
    use_tls: bool = True


def send_email(
    config: EmailConfig,
    to: str | list[str],
    subject: str,
    body: str,
    html: str | None = None,
    attachments: list[str | Path] | None = None,
    cc: str | list[str] | None = None,
) -> None:
    """Send email with optional HTML and attachments."""
    recipients = [to] if isinstance(to, str) else to
    cc_list = [cc] if isinstance(cc, str) else (cc or [])

    msg = MIMEMultipart("mixed")
    msg["From"] = config.username
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)

    # Body (plain text + optional HTML)
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(body, "plain", "utf-8"))
    if html:
        alt.attach(MIMEText(html, "html", "utf-8"))
    msg.attach(alt)

    # Attachments
    for file_path in attachments or []:
        path = Path(file_path)
        part = MIMEBase("application", "octet-stream")
        part.set_path(path)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{path.name}"')
        msg.attach(part)

    # Send
    all_recipients = recipients + cc_list
    with smtplib.SMTP(config.host, config.port) as server:
        if config.use_tls:
            server.starttls()
        server.login(config.username, config.password)
        server.sendmail(config.username, all_recipients, msg.as_string())


# --- Usage ---
config = EmailConfig(
    host="smtp.gmail.com",
    port=587,
    username="app@example.com",
    password="app-password",  # Use app-specific password
)

send_email(
    config=config,
    to="user@example.com",
    subject="Order Confirmed",
    body="Your order #123 has been confirmed.",
    html="<h1>Order Confirmed</h1><p>Your order <b>#123</b> has been confirmed.</p>",
    attachments=["invoice.pdf"],
)
```

## Common Mistakes

```python
# WRONG: Using plain text for HTML emails
msg = MIMEText("<h1>Hello</h1>", "plain")  # Shows raw HTML tags

# CORRECT: Use "html" content type
msg = MIMEText("<h1>Hello</h1>", "html")

# WRONG: Not using TLS
server = smtplib.SMTP("smtp.gmail.com", 587)
server.login(user, pw)  # Credentials sent in plain text!

# CORRECT: Start TLS before login
server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()  # Encrypt connection
server.login(user, pw)

# WRONG: Hardcoding credentials
config = EmailConfig(host="smtp.gmail.com", port=587, username="app@gmail.com", password="mypassword")

# CORRECT: Use environment variables
import os
config = EmailConfig(
    host=os.environ["SMTP_HOST"],
    port=int(os.environ.get("SMTP_PORT", "587")),
    username=os.environ["SMTP_USER"],
    password=os.environ["SMTP_PASSWORD"],
)
```

## Gotchas
- Gmail requires "App Passwords" (not regular password) when 2FA is enabled
- `server.sendmail()` expects a list of recipients, not a single string
- `MIMEMultipart("alternative")` lets the email client choose between plain text and HTML
- Attachments must be base64-encoded — `encoders.encode_base64()` handles this
- Port 587 = STARTTLS (preferred); Port 465 = SSL/TLS from start; Port 25 = unencrypted (avoid)
- `server.sendmail()` doesn't raise on invalid recipients — check `server.verify()` first
- For production, use services like SendGrid, SES, or Mailgun instead of raw SMTP
- `msg.as_string()` includes all headers, body, and attachments as a single RFC 2822 message

## Related
- python/concurrency/celery-basics.md
- python/web/fastapi/background-tasks.md
- python/stdlib/logging.md
