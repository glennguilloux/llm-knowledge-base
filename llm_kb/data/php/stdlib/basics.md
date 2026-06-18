---
id: "php-stdlib-basics"
title: "PHP 8.2+ Basics: Type Declarations, Match, and Null Coalescing"
language: "php"
category: "stdlib"
tags: ["php", "basics", "type-declarations", "match", "null-coalescing", "constructor-promotion"]
version: "8.2+"
retrieval_hint: "php type declarations match vs switch null coalescing spaceship operator constructor promotion readonly properties"
last_verified: "2026-05-24"
confidence: "high"
---

# PHP 8.2+ Basics: Type Declarations, Match, and Null Coalescing

## When to Use
- Writing modern PHP 8.2+ code
- Migrating from older PHP versions with deprecated patterns
- Understanding type declarations, union types, and intersection types
- Using `match` expression instead of `switch` statements

## Standard Pattern

```php
<?php

// Type declarations in function parameters and return types
function greet(string $name, int $times = 1): string {
    return str_repeat("Hello, $name! ", $times);
}

// Union types (PHP 8.0+)
function parseValue(string $input): int|float {
    return is_numeric($input) ? $input + 0 : 0;
}

// Nullable types
function findUser(int $id): ?User {
    return $this->repository->findById($id);  // Returns User or null
}

// Constructor property promotion (PHP 8.0+)
class User {
    public function __construct(
        private string $name,
        private string $email,
        private readonly int $id,       // readonly (PHP 8.1+)
        private ?int $age = null,       // Nullable with default
    ) {}
    
    public function getName(): string {
        return $this->name;
    }
}

// Match expression (PHP 8.0+) — preferred over switch
function getStatusCodeMessage(int $code): string {
    return match ($code) {
        200 => 'OK',
        201 => 'Created',
        400 => 'Bad Request',
        401 => 'Unauthorized',
        404 => 'Not Found',
        500 => 'Internal Server Error',
        default => 'Unknown Status',
    };
}

// Match can match conditions (not just values)
function describe(int $age): string {
    return match (true) {
        $age < 0 => 'Invalid',
        $age < 13 => 'Child',
        $age < 20 => 'Teenager',
        $age < 65 => 'Adult',
        default => 'Senior',
    };
}

// Null coalescing operator (??)
$config = $_ENV['DB_HOST'] ?? 'localhost';
$port = $_GET['port'] ?? 3306;  // Provides default if null or not set

// Null coalescing assignment (??=) (PHP 7.4+)
$settings['timeout'] ??= 30;  // Assign only if not already set

// Spaceship operator (<=>) for three-way comparison
$numbers = [3, 1, 4, 1, 5];
usort($numbers, fn($a, $b) => $a <=> $b);  // [-1, 0, 1]
// Returns -1 if $a < $b, 0 if equal, 1 if $a > $b

// Named arguments (PHP 8.0+)
$user = new User(
    name: 'Alice',
    email: 'alice@example.com',
    id: 1,
    age: 30,
);

// Fibers (PHP 8.1+) for cooperative multitasking
$fiber = new Fiber(function (): void {
    $value = Fiber::suspend('fiber');
    echo "Fiber resumed with: ", $value, "\n";
});
$value = $fiber->start();
$fiber->resume('test');
```

## Common Mistakes

```php
<?php

// WRONG: Not using type declarations (PHP 5 style)
function add($a, $b) {  // No types — accepts anything
    return $a + $b;
}
add("hello", "world");  // Runtime error or unexpected behavior

// CORRECT: Use type declarations
function add(int $a, int $b): int {
    return $a + $b;
}

// WRONG: Using switch when match is cleaner
switch ($status) {
    case 'pending':
        $message = 'Waiting';
        break;
    case 'approved':
        $message = 'Approved';
        break;
    default:
        $message = 'Unknown';
        break;
}

// CORRECT: Use match for value mapping
$message = match ($status) {
    'pending' => 'Waiting',
    'approved' => 'Approved',
    default => 'Unknown',
};

// WRONG: Not using constructor promotion (verbose)
class User {
    private string $name;
    private string $email;
    
    public function __construct(string $name, string $email) {
        $this->name = $name;
        $this->email = $email;
    }
}

// CORRECT: Constructor promotion is concise
class User {
    public function __construct(
        private string $name,
        private string $email,
    ) {}
}

// WRONG: Using isset() + ternary instead of ??
$host = isset($_ENV['DB_HOST']) ? $_ENV['DB_HOST'] : 'localhost';

// CORRECT: Use null coalescing operator
$host = $_ENV['DB_HOST'] ?? 'localhost';

// WRONG: Modifying readonly property after construction
class Config {
    public function __construct(public readonly string $apiKey) {}
}
$config = new Config('abc');
$config->apiKey = 'xyz';  // Error: Cannot modify readonly property

// CORRECT: Set readonly values only in constructor
```

## Gotchas
- `match` is an **expression** — it returns a value. `switch` is a statement.
- `match` uses strict comparison (`===`). `switch` uses loose comparison (`==`).
- `match` does NOT require `break` — it doesn't fall through.
- `readonly` properties (PHP 8.1+) can only be set once, in the constructor. They cannot be `unset` or modified after.
- Constructor promotion reduces boilerplate significantly. Use it for simple property assignment.
- `??` (null coalescing) checks if a value is null. It does NOT check for empty strings, 0, or false.
- Named arguments allow skipping optional parameters and improve readability.
- Union types (`int|float`) replace the need for multiple overloaded functions.
- `?Type` is shorthand for `Type|null`.

## Related
- php/stdlib/arrays.md
- php/stdlib/error-handling.md
- php/web/laravel-basics.md
