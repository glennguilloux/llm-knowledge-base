---
id: "security-input-sanitization"
title: "Input Sanitization and Safe Output"
language: "multi"
category: "security"
tags: ["input-sanitization", "security", "validation", "escaping", "safe-output", "xss", "sql-injection", "allowlist"]
version: "n/a"
retrieval_hint: "input sanitization validation escaping safe output allowlist context encoding HTML SQL URL file upload"
last_verified: "2026-06-20"
confidence: "medium"
---

# Input Sanitization and Safe Output

## When to Use
- Accepting user input for HTML, SQL, URLs, commands, or files
- Rendering untrusted content in web pages or API responses
- Building rich-text, search, filter, or upload features
- Reviewing code for safe output encoding and context-specific validation

## Standard Pattern

```python
# === Python: Validate, Sanitize, Then Encode for Context ===
import re
from html import escape
from urllib.parse import quote

ALLOWED_NAME_CHARS = re.compile(r"^[A-Za-z0-9 _.-]{1,80}$")

def sanitize_display_name(raw: str) -> str:
    value = raw.strip()
    if not ALLOWED_NAME_CHARS.fullmatch(value):
        raise ValueError("Invalid display name")
    return value

def render_user_name(name: str) -> str:
    return escape(name, quote=True)

def safe_query_param(value: str) -> str:
    return quote(value, safe="")
```

```typescript
// === TypeScript: Safe Rendering and URL Validation ===
function safeText(value: string): string {
  return value; // React text interpolation escapes by default
}

function safeUrl(value: string): string | null {
  try {
    const url = new URL(value);
    return url.protocol === "https:" ? url.toString() : null;
  } catch {
    return null;
  }
}
```

```python
# === Python: Rich Text Sanitization Before Rendering ===
import bleach

ALLOWED_TAGS = ["p", "br", "strong", "em", "ul", "ol", "li", "a"]
ALLOWED_ATTRS = {"a": ["href", "rel"]}

def sanitize_rich_text(raw_html: str) -> str:
    def link_callback(attrs, new=False):
        attrs["rel"] = "nofollow noopener"
        return attrs

    return bleach.clean(
        raw_html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=["https"],
        strip=True,
        linkify=True,
        linkify_callbacks=[link_callback],
    )
```

## Common Mistakes

```python
# WRONG: Trusting raw HTML for rendering
html_output = raw_html

# CORRECT: Sanitize with an allowlist before rendering
html_output = sanitize_rich_text(raw_html)
```

```python
# WRONG: Interpolating input into SQL
query = "SELECT * FROM users WHERE email = '" + email + "'"

# CORRECT: Use parameterized queries
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
```

```typescript
// WRONG: Rendering untrusted HTML directly
return <div dangerouslySetInnerHTML={{ __html: html }} />;

// CORRECT: Sanitize before rendering HTML
return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />;
```

```python
# WRONG: Treating validation as a substitute for output encoding
safe_output = user_input

# CORRECT: Validate input and encode for the output context
safe_output = escape(user_input, quote=True)
```

## Gotchas
- Sanitization is context-specific: HTML, JavaScript, CSS, SQL, and URLs each need different rules
- Input validation should happen at the boundary; output encoding should happen at the rendering boundary
- Rich-text sanitizers need allowlists for tags, attributes, protocols, and link behavior
- URL validation should check scheme and hostname, not only string prefixes
- File uploads need type validation and safe storage, not just extension checks
- Framework auto-escaping helps, but explicit escaping is still needed when bypassing it

## Related
- security/xss-prevention.md
- security/sql-injection-prevention.md
- security/web-security-basics.md
- security/owasp-top-10.md
