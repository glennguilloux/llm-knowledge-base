---
id: "php-stdlib-sessions-cookies"
title: "Sessions and Cookies: Security, Configuration, Best Practices"
language: "php"
category: "stdlib"
tags: ["php", "sessions", "cookies", "security", "http-only", "same-site"]
version: "8.1+"
retrieval_hint: "php sessions cookies secure flags session fixation HTTP-only SameSite"
last_verified: "2026-05-24"
confidence: "high"
---

# Sessions and Cookies: Security, Configuration, Best Practices

## When to Use
- Managing user sessions in PHP web applications
- Setting and reading cookies
- Implementing secure session handling
- Preventing session fixation and hijacking

## Standard Pattern

```php
<?php

// --- Secure Session Configuration ---
// Best done in php.ini or early in bootstrap:

// Session name (avoid default "PHPSESSID")
ini_set('session.name', 'APP_SESSION');

// Use secure cookies only
ini_set('session.cookie_secure', '1');       // HTTPS only
ini_set('session.cookie_httponly', '1');     // Not accessible via JavaScript
ini_set('session.cookie_samesite', 'Lax');   // CSRF protection
ini_set('session.cookie_domain', '');        // Current domain only
ini_set('session.cookie_path', '/');

// Session lifetime
ini_set('session.gc_maxlifetime', '7200');   // 2 hours
ini_set('session.cookie_lifetime', '0');      // Until browser closes

// Use strict mode
ini_set('session.use_strict_mode', '1');      // Reject uninitialized session IDs
ini_set('session.use_cookies', '1');
ini_set('session.use_only_cookies', '1');     // No URL-based session
ini_set('session.sid_length', '48');          // 48 chars = 192 bits
ini_set('session.sid_bits_per_character', '6'); // More entropy

// --- Starting a Session ---
// Must be called before any output
function startSecureSession(): void
{
    if (session_status() === PHP_SESSION_NONE) {
        session_start();
    }
}

// --- Regenerate Session ID (after login) ---
function regenerateSession(): void
{
    session_regenerate_id(true);  // true = delete old session
}

// --- Setting Session Data ---
session_start();
$_SESSION['user_id'] = 42;
$_SESSION['logged_in_at'] = time();
$_SESSION['ip_address'] = $_SERVER['REMOTE_ADDR'];

// --- Reading Session Data ---
$userId = $_SESSION['user_id'] ?? null;
if ($userId === null) {
    // Redirect to login
}

// --- Destroy Session (logout) ---
function destroySession(): void
{
    $_SESSION = [];  // Clear session data

    if (ini_get('session.use_cookies')) {
        $params = session_get_cookie_params();
        setcookie(
            session_name(),
            '',
            time() - 42000,
            $params['path'],
            $params['domain'],
            $params['secure'],
            $params['httponly']
        );
    }

    session_destroy();
}

// --- Setting Secure Cookies ---
function setSecureCookie(string $name, string $value, int $expiry = 0): bool
{
    return setcookie(
        $name,
        $value,
        [
            'expires' => $expiry ?: time() + 3600,
            'path' => '/',
            'domain' => '',
            'secure' => true,       // HTTPS only
            'httponly' => true,     // Not accessible via JS
            'samesite' => 'Lax',    // CSRF protection
        ]
    );
}

// --- Session Validation (optional, extra safety) ---
function validateSession(): bool
{
    if (!isset($_SESSION['created'])) {
        $_SESSION['created'] = time();
    } elseif (time() - $_SESSION['created'] > 1800) {
        // Regenerate session ID every 30 minutes
        session_regenerate_id(true);
        $_SESSION['created'] = time();
    }

    // Optional: validate IP (not for users behind load balancers)
    if (isset($_SESSION['ip_address'])) {
        if ($_SESSION['ip_address'] !== $_SERVER['REMOTE_ADDR']) {
            return false;  // Possible session hijacking
        }
    }

    return true;
}
```

## Common Mistakes

```php
<?php

// WRONG: Not regenerating session ID after login
session_start();
if (login($username, $password)) {
    $_SESSION['user_id'] = $user->id;
    // Session ID still has the old, pre-login value!
    // Vulnerable to session fixation attacks
}

// CORRECT: Regenerate after privilege escalation
session_start();
if (login($username, $password)) {
    session_regenerate_id(true);
    $_SESSION['user_id'] = $user->id;
}


// WRONG: Storing sensitive data in cookies
setcookie('user_id', '42', time() + 86400);
setcookie('role', 'admin', time() + 86400);  // Easily forged!

// CORRECT: Store a session identifier only, keep data server-side
setSecureCookie(session_name(), session_id(), 0);
// Data stored in $_SESSION on the server


// WRONG: Missing security flags on cookies
setcookie('token', $value, time() + 3600);
// Cookie sent over HTTP, accessible via JavaScript!

// CORRECT: Use secure flags
setcookie('token', $value, time() + 3600, '/', '', true, true);


// WRONG: Output before session_start()
echo "<html>";
session_start();  // Warning: session_start(): Cannot send session cookie
// Headers already sent!

// CORRECT: Start session before any output
session_start();
echo "<html>";


// WRONG: Not setting SameSite cookie attribute
// Vulnerable to CSRF attacks via cross-site requests

// CORRECT: Set SameSite
setcookie('session', $value, ['samesite' => 'Lax', ...]);
// Lax: sent for top-level GET navigation
// Strict: never sent cross-site (more secure, but breaks some flows)
// None: always sent (requires Secure flag)
```

## Gotchas
- **Session locking**: PHP locks the session file per-request. If you have concurrent AJAX requests, they run sequentially. Call `session_write_close()` after you're done writing to avoid blocking.
- **Garbage collection probability**: Session file cleanup runs with probability `session.gc_probability / session.gc_divisor` (default 1%). For high-traffic sites, implement a cron-based cleanup instead.
- **Headers already sent**: `session_start()` and `setcookie()` modify HTTP headers. Any output (including whitespace, BOM, or echo) before these calls will cause warnings.
- **Session fixation**: Attackers can set a victim's session ID before login. Always call `session_regenerate_id(true)` after any privilege level change.
- **Load balancers**: Shared session files don't work across multiple servers. Use Redis, Memcached, or database session handlers for distributed setups.
- **SameSite=None**: Requires `Secure` flag (HTTPS). Browsers reject SameSite=None without Secure. Chrome defaults to SameSite=Lax for cookies without SameSite attribute.
- **Session data serialization**: PHP serializes session data automatically. Custom objects stored in `$_SESSION` must be autoloadable or the session will fail to deserialize.

## Related
- php/stdlib/basics.md
- php/security/common-vulnerabilities.md
