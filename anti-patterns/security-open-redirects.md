---
id: "anti-patterns-security-open-redirects"
title: "Security Anti-Pattern: Open Redirect Vulnerabilities"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "security", "redirect", "phishing", "url-validation"]
version: "n/a"
retrieval_hint: "open redirect unvalidated URL redirect parameter phishing validate redirect target whitelist"
last_verified: "2026-05-24"
confidence: "high"
---

# Security Anti-Pattern: Open Redirect Vulnerabilities

## When to Use
- Implementing login/logout redirect flows
- Reviewing OAuth callback URLs
- Building "return to" or "next" URL parameters
- Security audits of URL handling logic

## Standard Pattern

```python
# WRONG: Unvalidated redirect (Flask)
@app.route("/login")
def login():
    next_url = request.args.get("next", "/")
    return redirect(next_url)  # Attacker: ?next=https://evil.com

# CORRECT: Validate redirect target (Flask)
from urllib.parse import urlparse

@app.route("/login")
def login():
    next_url = request.args.get("next", "/")
    # Only allow relative paths on same host
    parsed = urlparse(next_url)
    if parsed.netloc or parsed.scheme:
        next_url = "/"  # Reject absolute URLs
    return redirect(next_url)

# CORRECT: Allowlist approach
ALLOWED_HOSTS = {"app.example.com", "www.example.com"}

def is_safe_redirect(url: str) -> bool:
    parsed = urlparse(url)
    if not parsed.netloc:  # Relative URL
        return True
    return parsed.netloc in ALLOWED_HOSTS
```

```javascript
// WRONG: Unvalidated redirect (Express)
app.get('/auth/callback', (req, res) => {
  const returnTo = req.query.returnTo || '/';
  res.redirect(returnTo);  // Attacker: ?returnTo=https://evil.com
});

// CORRECT: Validate with allowlist (Express)
const { URL } = require('url');
const ALLOWED_HOSTS = new Set(['app.example.com']);

app.get('/auth/callback', (req, res) => {
  const returnTo = req.query.returnTo || '/';
  try {
    const parsed = new URL(returnTo, `https://${req.hostname}`);
    if (ALLOWED_HOSTS.has(parsed.hostname) || !parsed.hostname) {
      return res.redirect(returnTo);
    }
  } catch {}
  res.redirect('/');
});
```

```java
// WRONG: Unvalidated redirect (Spring)
@GetMapping("/login/success")
public String loginSuccess(@RequestParam String redirect) {
    return "redirect:" + redirect;  // ?redirect=https://phishing.com
}

// CORRECT: Whitelist validation (Spring)
@GetMapping("/login/success")
public String loginSuccess(@RequestParam String redirect) {
    UriComponentsBuilder uri = UriComponentsBuilder.fromUriString(redirect);
    String host = uri.build().getHost();
    if (host != null && !ALLOWED_HOSTS.contains(host)) {
        return "redirect:/dashboard";
    }
    return "redirect:" + redirect;
}
```

```python
# WRONG: SSRF via redirect proxy
@app.route("/proxy")
def proxy():
    url = request.args.get("url")
    response = requests.get(url)  # Server fetches attacker's URL
    return Response(response.content)

# CORRECT: Restrict internal requests
from ipaddress import ip_address

def is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    try:
        ip = ip_address(parsed.hostname)
        return ip.is_global  # Block private/loopback IPs
    except ValueError:
        return parsed.hostname in ALLOWED_HOSTS
```

## Common Mistakes
Open redirects occur when an application takes a user-supplied URL and redirects to it without validation. Attackers use these for phishing (redirecting to a fake login page that looks legitimate), OAuth token theft (redirecting the callback to steal auth codes), and SSRF (tricking the server into fetching internal resources). The fix is straightforward: validate redirect targets against an allowlist of trusted hosts, or restrict to relative paths only. Many frameworks provide built-in helpers (Django's `url_has_allowed_host_and_scheme`, Spring's `UriComponentsBuilder`) — use them instead of rolling your own.

## Gotchas
- Protocol-relative URLs (`//evil.com`) bypass scheme checks — always parse the full URL
- URL encoding (`%68%74%74%70%73`) and double-encoding can bypass naive string matching
- Backslashes (`https://evil.com\@app.example.com`) may be parsed differently by different libraries
- `javascript:` and `data:` URIs in redirect parameters can execute code — block non-HTTP schemes
- OAuth state parameter must be validated alongside the redirect_uri to prevent CSRF
- Relative paths like `//evil.com/path` are still absolute URLs — check for `//` prefix
- Some frameworks auto-redirect on 301/302 — validate in middleware, not just in route handlers

## Related
- security/web-security-basics.md
- python/web/fastapi/oauth2-password.md
- security/sso-saml-oidc.md
