---
id: "csharp-stdlib-error-handling"
title: "C# Error Handling: Exception Hierarchy, Custom Exceptions, and Result Pattern"
language: "csharp"
category: "stdlib"
tags: ["csharp", "error-handling", "exceptions", "custom-exceptions", "Result-pattern", "inner-exceptions"]
version: ".NET 8+"
retrieval_hint: "csharp exception hierarchy custom exceptions try catch finally exception filters inner exceptions Result pattern"
last_verified: "2026-05-24"
confidence: "high"
---

# C# Error Handling: Exception Hierarchy, Custom Exceptions, and Result Pattern

## When to Use
- Handling errors in C# applications
- Creating custom exception classes for domain errors
- Using exception filters for conditional catching
- Implementing the Result pattern for functional error handling

## Standard Pattern

```csharp
using System;

// Exception hierarchy
// System.Exception
//   → System.SystemException (CLR exceptions)
//     → ArgumentException, InvalidOperationException, etc.
//   → ApplicationException (custom exceptions — avoid, use Exception directly)

// Custom exceptions
public class ValidationException : Exception
{
    public string PropertyName { get; }
    public string Reason { get; }

    public ValidationException(string propertyName, string reason)
        : base($"Validation failed for '{propertyName}': {reason}")
    {
        PropertyName = propertyName;
        Reason = reason;
    }
}

public class NotFoundException : Exception
{
    public string ResourceType { get; }
    public object ResourceId { get; }

    public NotFoundException(string resourceType, object resourceId)
        : base($"{resourceType} with ID '{resourceId}' not found")
    {
        ResourceType = resourceType;
        ResourceId = resourceId;
    }
}

public class InsufficientFundsException : Exception
{
    public string AccountId { get; }
    public decimal Balance { get; }
    public decimal Requested { get; }

    public InsufficientFundsException(string accountId, decimal balance, decimal requested)
        : base($"Account '{accountId}' has insufficient funds: balance={balance:C}, requested={requested:C}")
    {
        AccountId = accountId;
        Balance = balance;
        Requested = requested;
    }
}

// Using custom exceptions
public User FindUser(int id)
{
    var user = repository.FindById(id);
    if (user == null)
        throw new NotFoundException(nameof(User), id);
    return user;
}

public void Transfer(string from, string to, decimal amount)
{
    var balance = GetBalance(from);
    if (balance < amount)
        throw new InsufficientFundsException(from, balance, amount);
    // Perform transfer...
}

// Exception filters (when clause)
try
{
    ProcessData(data);
}
catch (IOException ex) when (ex.HResult == -2147024864)
{
    // Handle "file in use" specifically
    Console.WriteLine("File is locked by another process");
}
catch (IOException ex) when (ex.Message.Contains("disk"))
{
    // Handle disk-related IO errors
    Console.WriteLine("Disk error");
}
catch (IOException ex)
{
    // Handle other IO errors
    Console.WriteLine($"IO error: {ex.Message}");
}

// Inner exceptions — preserve the original error
try
{
    var data = File.ReadAllText("config.json");
    config = JsonSerializer.Deserialize<Config>(data);
}
catch (JsonException ex)
{
    throw new ApplicationException("Failed to parse config.json", ex);
}

// Result pattern — functional error handling
public record Result<T>
{
    public T? Value { get; init; }
    public string? Error { get; init; }
    public bool IsSuccess { get; init; }

    public static Result<T> Success(T value) => new() { Value = value, IsSuccess = true };
    public static Result<T> Failure(string error) => new() { Error = error, IsSuccess = false };
}

// Using Result pattern
public Result<User> FindUserSafe(int id)
{
    try
    {
        var user = repository.FindById(id);
        return user != null
            ? Result<User>.Success(user)
            : Result<User>.Failure($"User {id} not found");
    }
    catch (Exception ex)
    {
        return Result<User>.Failure($"Database error: {ex.Message}");
    }
}

// Chaining Result operations
var result = FindUserSafe(1)
    .Map(u => u.Name)
    .Map(n => n.ToUpper());

// Extension methods for Result
public static class ResultExtensions
{
    public static Result<TResult> Map<T, TResult>(this Result<T> result, Func<T, TResult> mapper)
    {
        return result.IsSuccess
            ? Result<TResult>.Success(mapper(result.Value!))
            : Result<TResult>.Failure(result.Error!);
    }

    public static Result<TResult> FlatMap<T, TResult>(this Result<T> result, Func<T, Result<TResult>> mapper)
    {
        return result.IsSuccess ? mapper(result.Value!) : Result<TResult>.Failure(result.Error!);
    }
}

// try/catch/finally with return values
public string ReadConfig()
{
    try
    {
        return File.ReadAllText("config.json");
    }
    catch (FileNotFoundException)
    {
        return "{}";  // Default empty config
    }
    finally
    {
        Log("Config read attempted");
    }
}

// ExceptionDispatchInfo — rethrow without losing stack trace
ExceptionDispatchInfo? captured = null;
try
{
    RiskyOperation();
}
catch (Exception ex)
{
    captured = ExceptionDispatchInfo.Capture(ex);
}
// Later...
captured?.Throw();  // Preserves original stack trace
```

## Common Mistakes

```csharp
// WRONG: Catching Exception base class (too broad)
try
{
    ProcessData();
}
catch (Exception ex)  // Catches everything — including OutOfMemoryException!
{
    Console.WriteLine(ex.Message);
}

// CORRECT: Catch specific exceptions
try
{
    ProcessData();
}
catch (IOException ex)
{
    Console.WriteLine($"IO error: {ex.Message}");
}
catch (ArgumentException ex)
{
    Console.WriteLine($"Invalid argument: {ex.Message}");
}

// WRONG: Using ex.Message for user-facing errors
catch (Exception ex)
{
    ShowError(ex.Message);  // Technical message — not user-friendly!
}

// CORRECT: Use custom exceptions with user-friendly messages
catch (ValidationException ex)
{
    ShowError($"Please check {ex.PropertyName}: {ex.Reason}");
}

// WRONG: Rethrowing with throw ex (loses stack trace)
catch (Exception ex)
{
    throw ex;  // Stack trace is reset to this line!
}

// CORRECT: Use throw to preserve stack trace
catch (Exception)
{
    throw;  // Preserves original stack trace
}

// WRONG: Not using inner exceptions
catch (IOException ex)
{
    throw new ApplicationException("File error");  // Lost the original exception!
}

// CORRECT: Pass original exception as inner exception
catch (IOException ex)
{
    throw new ApplicationException("File error", ex);
}

// WRONG: Using exceptions for control flow
try
{
    var value = int.Parse(userInput);
}
catch (FormatException)
{
    value = 0;  // Using exception for normal flow!
}

// CORRECT: Use TryParse for expected failures
if (!int.TryParse(userInput, out var value))
{
    value = 0;
}
```

## Gotchas
- Custom exceptions should inherit from `Exception`, NOT `ApplicationException` (Microsoft recommends against `ApplicationException`).
- Use `throw;` (not `throw ex;`) to rethrow without losing the stack trace.
- `ExceptionDispatchInfo.Capture(ex).Throw()` preserves the stack trace across async boundaries.
- Exception filters (`when` clause) are evaluated before the catch block. They don't unwind the stack.
- `try/catch/finally`: `finally` always executes, even if `try` has a `return`.
- The Result pattern is an alternative to exceptions for expected failures. Use exceptions for exceptional cases.
- `InnerException` preserves the chain of exceptions. Always pass the inner exception when wrapping.
- `Environment.FailFast()` immediately terminates the application. Use for unrecoverable errors.
- `AggregateException` wraps multiple exceptions (from `Task.WhenAll`, `Parallel.ForEach`).

## Related
- csharp/stdlib/async-advanced.md
- csharp/stdlib/linq-advanced.md
- csharp/stdlib/reflection-attributes.md
