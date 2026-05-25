---
id: "php-db-pdo"
title: "PHP PDO: Prepared Statements, Transactions, and Error Handling"
language: "php"
category: "db"
tags: ["php", "pdo", "database", "prepared-statements", "sql-injection", "transactions"]
version: "8.2+"
retrieval_hint: "php PDO connection prepared statements SQL injection prevention transactions fetching modes error handling"
last_verified: "2026-05-24"
confidence: "high"
---

# PHP PDO: Prepared Statements, Transactions, and Error Handling

## When to Use
- Connecting to databases in PHP
- Preventing SQL injection with prepared statements
- Managing database transactions
- Working with multiple database types (MySQL, PostgreSQL, SQLite)

## Standard Pattern

```php
<?php

// PDO connection with proper error handling
function createConnection(): PDO
{
    $host = $_ENV['DB_HOST'] ?? 'localhost';
    $db = $_ENV['DB_NAME'] ?? 'mydb';
    $user = $_ENV['DB_USER'] ?? 'root';
    $pass = $_ENV['DB_PASS'] ?? '';
    $charset = 'utf8mb4';

    $dsn = "mysql:host={$host};dbname={$db};charset={$charset}";
    
    $options = [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,  // Throw exceptions on errors
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,        // Fetch associative arrays
        PDO::ATTR_EMULATE_PREPARES   => false,                   // Use real prepared statements
        PDO::ATTR_STRINGIFY_FETCHES  => false,                   // Keep native types
    ];

    try {
        return new PDO($dsn, $user, $pass, $options);
    } catch (PDOException $e) {
        throw new RuntimeException('Database connection failed: ' . $e->getMessage());
    }
}

// Prepared statements — ALWAYS use for user input
function findUserByEmail(PDO $pdo, string $email): ?array
{
    $stmt = $pdo->prepare('SELECT * FROM users WHERE email = :email');
    $stmt->execute(['email' => $email]);
    return $stmt->fetch() ?: null;
}

function createUser(PDO $pdo, string $name, string $email, string $password): int
{
    $stmt = $pdo->prepare(
        'INSERT INTO users (name, email, password) VALUES (:name, :email, :password)'
    );
    $stmt->execute([
        'name'     => $name,
        'email'    => $email,
        'password' => password_hash($password, PASSWORD_ARGON2ID),
    ]);
    return (int) $pdo->lastInsertId();
}

// Fetching multiple rows
function getActiveUsers(PDO $pdo): array
{
    $stmt = $pdo->prepare('SELECT id, name, email FROM users WHERE active = :active');
    $stmt->execute(['active' => true]);
    return $stmt->fetchAll();
}

// Fetching a single column
function getUserNames(PDO $pdo): array
{
    $stmt = $pdo->query('SELECT name FROM users ORDER BY name');
    return $stmt->fetchAll(PDO::FETCH_COLUMN);
}

// Transactions
function transfer(PDO $pdo, int $fromId, int $toId, float $amount): void
{
    $pdo->beginTransaction();
    try {
        // Deduct from sender
        $stmt = $pdo->prepare('UPDATE accounts SET balance = balance - :amount WHERE id = :id');
        $stmt->execute(['amount' => $amount, 'id' => $fromId]);
        
        if ($stmt->rowCount() === 0) {
            throw new RuntimeException('Sender account not found');
        }
        
        // Add to receiver
        $stmt = $pdo->prepare('UPDATE accounts SET balance = balance + :amount WHERE id = :id');
        $stmt->execute(['amount' => $amount, 'id' => $toId]);
        
        if ($stmt->rowCount() === 0) {
            throw new RuntimeException('Receiver account not found');
        }
        
        $pdo->commit();
    } catch (Exception $e) {
        $pdo->rollBack();
        throw $e;
    }
}

// IN clause with dynamic parameters
function getUsersByIds(PDO $pdo, array $ids): array
{
    $placeholders = implode(',', array_fill(0, count($ids), '?'));
    $stmt = $pdo->prepare("SELECT * FROM users WHERE id IN ({$placeholders})");
    $stmt->execute($ids);
    return $stmt->fetchAll();
}

// Pagination
function getUsersPage(PDO $pdo, int $page = 1, int $perPage = 20): array
{
    $offset = ($page - 1) * $perPage;
    $stmt = $pdo->prepare('SELECT * FROM users ORDER BY id LIMIT :limit OFFSET :offset');
    $stmt->bindValue('limit', $perPage, PDO::PARAM_INT);
    $stmt->bindValue('offset', $offset, PDO::PARAM_INT);
    $stmt->execute();
    return $stmt->fetchAll();
}

// Count query
function countUsers(PDO $pdo): int
{
    return (int) $pdo->query('SELECT COUNT(*) FROM users')->fetchColumn();
}
```

## Common Mistakes

```php
<?php

// WRONG: String concatenation for SQL (SQL injection vulnerability!)
$email = $_GET['email'];
$stmt = $pdo->query("SELECT * FROM users WHERE email = '$email'");
// Attacker can send: email = "'; DROP TABLE users; --"

// CORRECT: Always use prepared statements
$stmt = $pdo->prepare('SELECT * FROM users WHERE email = :email');
$stmt->execute(['email' => $_GET['email']]);

// WRONG: Not setting ERRMODE_EXCEPTION
$pdo = new PDO($dsn, $user, $pass);
// Errors are silently ignored! Queries fail without any indication.

// CORRECT: Always set ERRMODE_EXCEPTION
$pdo = new PDO($dsn, $user, $pass, [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
]);

// WRONG: Using emulated prepared statements (default in MySQL)
// PDO emulates prepares by default — it does string escaping, not real prepares

// CORRECT: Disable emulation for real prepared statements
$pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, false);

// WRONG: Not using transactions for related operations
$pdo->exec('UPDATE accounts SET balance = balance - 100 WHERE id = 1');
// If this fails, the second query runs without the first!
$pdo->exec('UPDATE accounts SET balance = balance + 100 WHERE id = 2');

// CORRECT: Wrap related operations in a transaction
$pdo->beginTransaction();
try {
    $pdo->exec('UPDATE accounts SET balance = balance - 100 WHERE id = 1');
    $pdo->exec('UPDATE accounts SET balance = balance + 100 WHERE id = 2');
    $pdo->commit();
} catch (Exception $e) {
    $pdo->rollBack();
    throw $e;
}

// WRONG: Not binding LIMIT/OFFSET as INT (PDO treats all params as STRING by default)
$stmt = $pdo->prepare('SELECT * FROM users LIMIT ? OFFSET ?');
$stmt->execute([20, 0]);  // May cause type issues in some databases

// CORRECT: Bind with explicit type for LIMIT/OFFSET
$stmt->bindValue(1, 20, PDO::PARAM_INT);
$stmt->bindValue(2, 0, PDO::PARAM_INT);
$stmt->execute();
```

## Gotchas
- **NEVER** concatenate user input into SQL queries. Always use prepared statements with bound parameters.
- `PDO::ATTR_EMULATE_PREPARES => false` ensures real prepared statements at the database level.
- `PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION` makes PDO throw exceptions instead of silent failures.
- `PDO::FETCH_ASSOC` returns associative arrays (no numeric keys). Default is `FETCH_BOTH` (duplicated).
- Transactions: always use `beginTransaction()` + `commit()`/`rollBack()` in try/catch.
- `lastInsertId()` returns the auto-increment ID of the last INSERT.
- `rowCount()` returns affected rows for UPDATE/DELETE. For SELECT, use `fetchAll()` and `count()`.
- For `LIMIT`/`OFFSET`, bind with `PDO::PARAM_INT` to avoid type coercion issues.
- `PDO::ATTR_STRINGIFY_FETCHES => false` preserves native PHP types (int, float) instead of returning everything as strings.

## Related
- php/stdlib/basics.md
- php/stdlib/error-handling.md
- php/web/laravel-basics.md
- php/security/common-vulnerabilities.md
