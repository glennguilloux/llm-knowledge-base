---
id: "php-stdlib-error-handling"
title: "PHP Error Handling: Exceptions, Throwable, and Custom Exceptions"
language: "php"
category: "stdlib"
tags: ["php", "error-handling", "exceptions", "throwable", "try-catch", "custom-exceptions"]
version: "8.2+"
retrieval_hint: "php try catch finally custom exceptions Throwable set_exception_handler error reporting"
last_verified: "2026-05-24"
confidence: "high"
---

# PHP Error Handling: Exceptions, Throwable, and Custom Exceptions

## When to Use
- Handling runtime errors in PHP applications
- Creating custom exception classes for domain errors
- Setting up global exception handling
- Understanding the difference between Error and Exception in PHP 7+

## Standard Pattern

```php
<?php

// Basic try/catch/finally
function divide(float $a, float $b): float {
    if ($b === 0.0) {
        throw new InvalidArgumentException('Division by zero');
    }
    return $a / $b;
}

try {
    $result = divide(10, 0);
} catch (InvalidArgumentException $e) {
    echo "Invalid argument: " . $e->getMessage();
} catch (Exception $e) {
    echo "General error: " . $e->getMessage();
} finally {
    // Always executes — cleanup code here
    echo "Done.\n";
}

// Custom exception classes
class ValidationException extends RuntimeException {
    private array $errors;
    
    public function __construct(array $errors, string $message = 'Validation failed') {
        parent::__construct($message);
        $this->errors = $errors;
    }
    
    public function getErrors(): array {
        return $this->errors;
    }
}

class NotFoundException extends RuntimeException {
    public function __construct(string $resource, int|int|string $id) {
        parent::__construct("{$resource} with ID {$id} not found");
    }
}

class InsufficientFundsException extends RuntimeException {
    public function __construct(
        public readonly string $accountId,
        public readonly float $balance,
        public readonly float $requested,
    ) {
        parent::__construct(
            "Account {$accountId}: balance={$balance}, requested={$requested}"
        );
    }
}

// Using custom exceptions
function findUser(int $id): User {
    $user = User::find($id);
    if (!$user) {
        throw new NotFoundException('User', $id);
    }
    return $user;
}

function transfer(string $from, string $to, float $amount): void {
    $balance = getBalance($from);
    if ($balance < $amount) {
        throw new InsufficientFundsException($from, $balance, $amount);
    }
    // Perform transfer...
}

// Catching multiple exception types (PHP 8.0+)
try {
    $user = findUser(999);
} catch (NotFoundException|ValidationException $e) {
    echo "Domain error: " . $e->getMessage();
} catch (Throwable $e) {
    // Catches both Exception and Error
    echo "Unexpected error: " . $e->getMessage();
}

// Global exception handler
set_exception_handler(function (Throwable $e): void {
    error_log(sprintf(
        "[%s] %s in %s:%d\n%s",
        date('Y-m-d H:i:s'),
        $e->getMessage(),
        $e->getFile(),
        $e->getLine(),
        $e->getTraceAsString()
    ));
    
    http_response_code(500);
    echo json_encode(['error' => 'Internal Server Error']);
});

// Error reporting configuration
error_reporting(E_ALL);           // Report all errors
ini_set('display_errors', '0');   // Don't display to users (production)
ini_set('log_errors', '1');       // Log errors to file
ini_set('error_log', '/var/log/php_errors.log');

// Converting errors to exceptions (PHP 8+)
// set_error_handler(function ($severity, $message, $file, $line) {
//     throw new ErrorException($message, 0, $severity, $file, $line);
// });

// Try-catch with return value
function parseConfig(string $json): array {
    try {
        return json_decode($json, true, 512, JSON_THROW_ON_ERROR);
    } catch (JsonException $e) {
        throw new RuntimeException('Config parse failed: ' . $e->getMessage(), 0, $e);
    }
}
```

## Common Mistakes

```php
<?php

// WRONG: Catching Exception instead of Throwable (PHP 7+)
try {
    $result = 1 / 0;  // DivisionByZeroError (extends Error, not Exception)
} catch (Exception $e) {
    // Does NOT catch Error! DivisionByZeroError slips through
}

// CORRECT: Catch Throwable to handle both Exception and Error
try {
    $result = 1 / 0;
} catch (Throwable $e) {
    echo "Caught: " . $e->getMessage();
}

// WRONG: Empty catch block (silently swallowing errors)
try {
    riskyOperation();
} catch (Exception $e) {
    // Nothing here — error is silently lost!
}

// CORRECT: Always handle or log the exception
try {
    riskyOperation();
} catch (Exception $e) {
    logger()->error('Operation failed: ' . $e->getMessage());
    throw new RuntimeException('Operation failed', 0, $e);  // Re-throw with context
}

// WRONG: Not using finally for cleanup
$handle = fopen('file.txt', 'r');
try {
    $data = fread($handle, 1024);
    if (somethingFails()) {
        throw new RuntimeException('Failed');
    }
} catch (Exception $e) {
    throw $e;
}
// File handle may not be closed if exception thrown!

// CORRECT: Use finally for cleanup
$handle = fopen('file.txt', 'r');
try {
    $data = fread($handle, 1024);
} catch (Exception $e) {
    throw $e;
} finally {
    fclose($handle);  // Always closed
}

// WRONG: Throwing generic Exception
throw Exception('Something went wrong');  // No type, no context

// CORRECT: Throw specific exception with context
throw new InsufficientFundsException($accountId, $balance, $amount);
```

## Gotchas
- In PHP 7+, `Error` and `Exception` both implement `Throwable`. Catch `Throwable` to handle both.
- `Error` is for internal PHP errors (TypeError, ParseError, ArithmeticError). These used to be fatal errors in PHP 5.
- `finally` block always executes, even if `try` has a `return` statement.
- Custom exceptions should domain-specific and carry context in their properties.
- `JSON_THROW_ON_ERROR` flag on `json_decode()` throws `JsonException` instead of returning null + error codes.
- `error_reporting()` controls which errors are reported. `display_errors` controls output.
- In production, always set `display_errors = 0` and `log_errors = 1`.
- Exception chaining: pass the previous exception as the third argument `new RuntimeException('msg', 0, $previousException)`.
- PHP 8.0 allows `catch (Type1|Type2)` multi-catch syntax.

## Related
- php/stdlib/basics.md
- php/web/laravel-basics.md
- php/security/common-vulnerabilities.md
