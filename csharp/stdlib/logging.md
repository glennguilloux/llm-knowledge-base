---
id: "csharp-stdlib-logging"
title: "Logging in .NET: ILogger, Serilog, Structured Logging, Scopes"
language: "csharp"
category: "stdlib"
tags: ["csharp", "logging", "serilog", "structured-logging", "ilogger", "scopes"]
version: "8.0+"
retrieval_hint: "csharp dotnet logging Serilog ILogger structured logging scopes seq"
last_verified: "2026-05-24"
confidence: "high"
---

# Logging in .NET: ILogger, Serilog, Structured Logging, Scopes

## When to Use
- Adding structured logging to .NET applications
- Using the built-in `ILogger<T>` abstraction
- Configuring Serilog for advanced logging
- Adding contextual information with log scopes
- Centralizing log configuration

## Standard Pattern

```csharp
using Microsoft.Extensions.Logging;
using Serilog;
using Serilog.Formatting.Json;
using System;
using System.Collections.Generic;

// --- Program.cs — Logger Configuration ---
var builder = WebApplication.CreateBuilder(args);

// Clear default providers and add Serilog
builder.Logging.ClearProviders();
builder.Logging.AddConsole();
builder.Logging.AddDebug();
builder.Logging.AddEventLog();

// Or use Serilog directly:
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Information()
    .MinimumLevel.Override("Microsoft", LogEventLevel.Warning)
    .MinimumLevel.Override("Microsoft.AspNetCore", LogEventLevel.Error)
    .Enrich.FromLogContext()
    .Enrich.WithMachineName()
    .Enrich.WithThreadId()
    .WriteTo.Console()
    .WriteTo.File(
        "logs/app-.log",
        rollingInterval: RollingInterval.Day,
        retainedFileCountLimit: 30,
        formatProvider: null)
    .WriteTo.Seq("http://localhost:5341")
    .CreateLogger();

builder.Host.UseSerilog();  // Replace .NET logging with Serilog

// --- Using ILogger<T> in a Service ---
public class OrderService
{
    private readonly ILogger<OrderService> _logger;

    public OrderService(ILogger<OrderService> logger)
    {
        _logger = logger;
    }

    public async Task<Order> CreateOrderAsync(OrderRequest request)
    {
        // Structured logging — use placeholders, not interpolation!
        _logger.LogInformation(
            "Creating order for customer {CustomerId} with {ItemCount} items",
            request.CustomerId,
            request.Items.Count);

        try
        {
            var order = await SaveOrderAsync(request);

            _logger.LogInformation(
                "Order {OrderId} created successfully for customer {CustomerId}",
                order.Id,
                request.CustomerId);

            return order;
        }
        catch (Exception ex)
        {
            _logger.LogError(
                ex,
                "Failed to create order for customer {CustomerId}",
                request.CustomerId);
            throw;
        }
    }
}

// --- Log Levels ---
// Trace      = 0 (Most detailed, rarely used in production)
// Debug      = 1 (Diagnostic info, enabled in dev)
// Information = 2 (Normal flow of the application)
// Warning    = 3 (Unexpected but not an error)
// Error      = 4 (Recoverable failures)
// Critical   = 5 (Unrecoverable failures, system crash)

// --- Log Scopes ---
// Scopes add context to all logs within a block
public class RequestHandler
{
    private readonly ILogger<RequestHandler> _logger;

    public async Task HandleRequestAsync(string requestId, string userId)
    {
        // BeginScope returns IDisposable — dispose to leave scope
        using (_logger.BeginScope(new Dictionary<string, object>
        {
            ["RequestId"] = requestId,
            ["UserId"] = userId,
        }))
        {
            _logger.LogInformation("Processing request");  // Includes scope

            await ProcessInternalAsync();

            _logger.LogInformation("Request completed");  // Also includes scope
        }
        // Scope ends here — subsequent logs don't have RequestId/UserId
    }
}

// --- Category Names ---
// ILogger<OrderService> has category = "OrderService" (full type name)
// ILoggerFactory.CreateLogger("MyModule") for custom categories

// --- Minimum Level Overrides (filtering by category) ---
builder.Logging.AddFilter("Microsoft", LogLevel.Warning);  // Suppress framework
builder.Logging.AddFilter("System", LogLevel.Warning);
builder.Logging.AddFilter("MyApp.HealthChecks", LogLevel.Debug);  // Be verbose for my code

// --- Best Practice: Extension Methods ---
// Use these helper methods for common scenarios
// _logger.LogTrace("...");
// _logger.LogDebug("...");
// _logger.LogInformation("...");
// _logger.LogWarning("...");
// _logger.LogError(ex, "...");
// _logger.LogCritical(ex, "...");
```

## Common Mistakes

```csharp
// WRONG: String interpolation instead of structured templates
_logger.LogInformation($"User {userId} logged in at {DateTime.UtcNow}");
// Logs the string as-is — can't search/filter by userId!

// CORRECT: Structured logging with placeholders
_logger.LogInformation("User {UserId} logged in at {LoginTime}", userId, DateTime.UtcNow);
// Structured: UserId and LoginTime are separate fields — searchable


// WRONG: Logging sensitive data
_logger.LogInformation("User password: {Password}", password);  // Security risk!

// CORRECT: Never log sensitive data
_logger.LogInformation("Password reset requested for user {UserId}", userId);


// WRONG: Not using exception overload
try { /* ... */ }
catch (Exception ex)
{
    _logger.LogError("Error: " + ex.Message);  // Lost stack trace!
}

// CORRECT: Pass exception as first parameter
catch (Exception ex)
{
    _logger.LogError(ex, "Failed to process order {OrderId}", orderId);
}


// WRONG: Missing scope disposal (scope never ends)
public void Process()
{
    _logger.BeginScope("RequestScope");  // Never disposed!
    _logger.LogInformation("Processing");
}
// Scope continues for the lifetime of the logger instance!

// CORRECT: Use using for scopes
public void Process()
{
    using (_logger.BeginScope("RequestScope"))
    {
        _logger.LogInformation("Processing");
    }
    // Scope ends here
}


// WRONG: Logging and throwing (duplicate logging)
catch (Exception ex)
{
    _logger.LogError(ex, "Error occurred");
    throw;  // Global handler logs again — duplicate!
}

// CORRECT: Let the global handler log once
catch (Exception)
{
    // Log only if you have context the global handler doesn't
    _logger.LogWarning("Context-specific warning for order {OrderId}", id);
    throw;
}
```

## Gotchas
- **Async local scope with async/await**: `BeginScope` uses `AsyncLocal` — the scope flows with the execution context. If you create a scope in a parent method, it applies to all child async operations. Dispose the scope to prevent it from leaking.
- **Exception logging overloads**: The first parameter to `LogError` should be the exception. Then the message template. The exception's `ToString()` is automatically included. Don't pass the exception as a structured value.
- **Category names for filtering**: The logger category (typically the full type name) is used for filtering. Use `ILogger<T>` where `T` is your class. For generic filters, use `ILoggerFactory` with a custom category name.
- **Serilog enrichers**: Enrichers add global properties to every log event. `FromLogContext()` enables scope properties. `WithMachineName()` adds the machine name. Enricher ordering can affect performance.
- **Log level in production**: Set minimum level to `Warning` or `Information` in production. `Debug` and `Trace` generate too much data and affect performance. Use `appsettings.json` to control log levels without recompilation.
- **File logging rotation**: Use rolling file sinks to prevent disk full issues. Configure `retainedFileCountLimit` and `fileSizeLimitBytes` for production file logs.
- **Structured logging backends**: Serilog structured output (JSON, Seq, Elasticsearch) enables powerful log analysis. Console logging loses structure — always use a structured sink for production.

## Related
- csharp/stdlib/configuration.md
- csharp/web/aspnet-basics.md
- csharp/stdlib/dependency-injection.md
