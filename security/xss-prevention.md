---
id: "security-xss-prevention"
title: "Cross-Site Scripting (XSS) Prevention"
language: "multi"
category: "security"
tags: ["xss", "security", "cross-site-scripting", "csp", "sanitization", "output-encoding"]
version: "n/a"
retrieval_hint: "XSS cross-site scripting prevention CSP Content Security Policy sanitization output encoding DOM injection reflected stored"
last_verified: "2026-05-24"
confidence: "high"
---

# Cross-Site Scripting (XSS) Prevention

## When to Use
- Rendering user-provided content in HTML pages
- Building template engines or rich-text editors
- Setting up Content Security Policy headers
- Reviewing frontend code for injection vectors

## Standard Pattern

```typescript
// === React: Auto-escaping protects against XSS by default ===

// CORRECT: JSX auto-escapes all interpolated values
function UserComment({ text }: { text: string }) {
    return <div className="comment">{text}</div>;
    // Even if text = "<script>alert('xss')</script>", it's rendered as text, not HTML
}

// CORRECT: Using dangerouslySetInnerHTML WITH sanitization
import DOMPurify from "dompurify";

function RichContent({ html }: { html: string }) {
    const clean = DOMPurify.sanitize(html, {
        ALLOWED_TAGS: ["b", "i", "em", "strong", "a", "p", "br", "ul", "ol", "li"],
        ALLOWED_ATTR: ["href", "target"],
    });
    return <div dangerouslySetInnerHTML={{ __html: clean }} />;
}
```

```python
# === Python (Jinja2/Django): Template auto-escaping ===

# CORRECT: Jinja2 auto-escapes by default in .html templates
# template.html:
# <div>{{ user_input }}</div>  {# Auto-escaped — safe #}

# CORRECT: Explicitly mark safe only when you've sanitized
from markupsafe import Markup
import bleach

def render_user_bio(raw_html: str) -> Markup:
    clean = bleach.clean(
        raw_html,
        tags=["b", "i", "a", "p", "br"],
        attributes={"a": ["href"]},
    )
    return Markup(clean)

# Django templates auto-escape by default:
# {{ user_input }}          <- auto-escaped
# {{ user_input|safe }}     <- NOT escaped — only use with sanitized content
```

```java
// === Java: Output encoding with OWASP Encoder ===

import org.owasp.encoder.Encode;

// CORRECT: Encode for different contexts
String safeHtml = Encode.forHtml(userInput);        // HTML body context
String safeAttr = Encode.forHtmlAttribute(userInput); // HTML attribute
String safeJs = Encode.forJavaScript(userInput);     // JavaScript string
String safeUrl = Encode.forUriComponent(userInput);   // URL parameter

// CORRECT: In JSP
// <div>${fn:escapeXml(userInput)}</div>
```

```typescript
// === Content Security Policy (CSP) — the strongest XSS defense ===

// CORRECT: Strict CSP via HTTP header (or meta tag)
const CSP_HEADER = [
    "default-src 'self'",
    "script-src 'self'",              // No inline scripts
    "style-src 'self' 'unsafe-inline'", // Inline styles often needed
    "img-src 'self' data: https:",
    "font-src 'self'",
    "connect-src 'self' https://api.example.com",
    "frame-ancestors 'none'",          // Prevent clickjacking
    "base-uri 'self'",
    "form-action 'self'",
].join("; ");

// Express middleware
app.use((req, res, next) => {
    res.setHeader("Content-Security-Policy", CSP_HEADER);
    next();
});
```

```python
# === Sanitizing HTML with bleach (Python) ===

import bleach

ALLOWED_TAGS = ["b", "i", "strong", "em", "a", "p", "br", "ul", "ol", "li", "code", "pre"]
ALLOWED_ATTRS = {"a": ["href", "title", "rel"]}

def sanitize_html(raw: str) -> str:
    """Sanitize user-submitted HTML to prevent XSS."""
    cleaned = bleach.clean(
        raw,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        strip=True,  # Strip disallowed tags instead of escaping
    )
    # Force rel=nofollow on links to prevent phishing
    return bleach.linkify(cleaned, callbacks=[lambda attrs: attrs])

# CORRECT: Always sanitize on OUTPUT (rendering), not just input
# Reason: context matters — what's safe in HTML may be unsafe in JS
```

## Common Mistakes

```javascript
// WRONG: Using innerHTML with user input
document.getElementById("output").innerHTML = userInput;  // XSS!

// CORRECT: Use textContent
document.getElementById("output").textContent = userInput;

// WRONG: Inserting user input into href or src attributes
<a href={userUrl}>Click me</a>  // javascript:alert(1) works!

// CORRECT: Validate URL protocol
function SafeLink({ url, children }: { url: string; children: React.ReactNode }) {
    if (!url.startsWith("https://") && !url.startsWith("/")) {
        return <span>{children}</span>;  // Don't render suspicious URLs
    }
    return <a href={url}>{children}</a>;
}
```

```python
# WRONG: Marking user input as safe without sanitizing
from markupsafe import Markup
template.render(content=Markup(user_input))  # XSS!

# CORRECT: Sanitize THEN mark safe
clean = bleach.clean(user_input, tags=["b", "i", "p"])
template.render(content=Markup(clean))

# WRONG: Building URLs from user input without validation
url = f"https://api.example.com/{user_path}"  // Can inject javascript: protocol

# CORRECT: Validate and encode URL components
from urllib.parse import quote
safe_path = quote(user_path, safe="")
```

```typescript
// WRONG: dangerouslySetInnerHTML without sanitization
<div dangerouslySetInnerHTML={{ __html: userInput }} />  // Direct XSS!

// CORRECT: Sanitize first
import DOMPurify from "dompurify";
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userInput) }} />
```

```python
# WRONG: Using |safe filter in Django templates with untrusted content
# {{ user_bio|safe }}  {# If user_bio contains <script>, it runs! #}

# CORRECT: Let Django auto-escape (default behavior)
# {{ user_bio }}  {# Auto-escaped — safe #}
```

## Gotchas
- React's JSX auto-escapes `{variable}` but NOT `dangerouslySetInnerHTML` — never use it without DOMPurify
- DOM-based XSS happens entirely client-side — the server never sees the malicious payload
- CSP `unsafe-inline` for scripts defeats most of CSP's XSS protection — avoid it
- Template engines (Jinja2, Django, Twig) auto-escape by default — but `|safe`, `Markup()`, `{!! !!}` bypass it
- `javascript:` URLs in `<a href>` are an XSS vector — validate URL schemes
- Sanitization should happen at OUTPUT time (rendering), not input time — different contexts need different encoding
- Stored XSS is more dangerous than reflected — the payload persists and hits every user
- `eval()`, `new Function()`, and `document.write()` are always XSS vectors with user input
- SVG files can contain JavaScript — sanitize uploaded SVGs or serve them with `Content-Disposition: attachment`
- URL encoding (`encodeURIComponent`) is NOT the same as HTML encoding — use the right one for the context

## Related
- security/web-security-basics.md
- security/owasp-top-10.md
- security/csrf-protection.md
- security/https-tls-must-know.md
