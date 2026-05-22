---
id: "csharp-web-aspnet-middleware"
title: "ASP.NET Core Middleware Pipeline"
language: "csharp"
category: "web"
subcategory: "api-framework"
tags: ["csharp", "dotnet", "aspnet", "middleware", "pipeline", "request", "exception"]
version: "8.0+"
retrieval_hint: "ASP.NET middleware pipeline UseWhen exception handler request logging"
last_verified: "2026-05-22"
confidence: "high"
---

# ASP.NET Core Middleware Pipeline

## When to Use
- Cross-cutting concerns: logging, authentication, error handling, CORS
- Request/response transformation before reaching endpoints
- Short-circuiting requests (rate limiting, auth checks)
- Adding headers, correlation IDs, or timing to every response

## Standard Pattern

```csharp
// Program.cs — middleware registration order matters
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddScoped<IMyService, MyService>();

var app = builder.Build();

// 1. Exception handler FIRST (catches all downstream errors)
app.UseExceptionHandler("/error");

// 2. HSTS and HTTPS redirection
if (!app.Environment.IsDevelopment())
{
    app.UseHsts();
}
app.UseHttpsRedirection();

// 3. Static files (short-circuits if file found)
app.UseStaticFiles();

// 4. Routing (matches endpoint but doesn't execute yet)
app.UseRouting();

// 5. CORS (before auth)
app.UseCors("AllowSpecificOrigins");

// 6. Authentication (who are you?)
app.UseAuthentication();

// 7. Authorization (are you allowed?)
app.UseAuthorization();

// 8. Custom middleware
app.UseMiddleware<RequestLoggingMiddleware>();
app.UseMiddleware<CorrelationIdMiddleware>();

// 9. Rate limiting
app.UseRateLimiter();

// 10. Endpoints
app.MapControllers();

app.Run();
```

## Custom Middleware

```csharp
// Request logging middleware — class-based approach
public class RequestLoggingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<RequestLoggingMiddleware> _logger;

    public RequestLoggingMiddleware(RequestDelegate next, ILogger<RequestLoggingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var stopwatch = Stopwatch.StartNew();
        var method = context.Request.Method;
        var path = context.Request.Path;

        try
        {
            await _next(context);
            stopwatch.Stop();

            _logger.LogInformation(
                "HTTP {Method} {Path} responded {StatusCode} in {ElapsedMs}ms",
                method, path, context.Response.StatusCode, stopwatch.ElapsedMilliseconds);
        }
        catch (Exception)
        {
            stopwatch.Stop();
            _logger.LogError(
                "HTTP {Method} {Path} failed after {ElapsedMs}ms",
                method, path, stopwatch.ElapsedMilliseconds);
            throw;
        }
    }
}

// Correlation ID middleware — inline approach
app.Use(async (context, next) =>
{
    var correlationId = context.Request.Headers["X-Correlation-ID"].FirstOrDefault()
        ?? Guid.NewGuid().ToString();

    context.Items["CorrelationId"] = correlationId;
    context.Response.Headers["X-Correlation-ID"] = correlationId;

    using (LogContext.PushProperty("CorrelationId", correlationId))
    {
        await next();
    }
});

// Conditional middleware with UseWhen
app.UseWhen(
    context => context.Request.Path.StartsWithSegments("/api"),
    appBuilder =>
    {
        appBuilder.UseMiddleware<ApiKeyValidationMiddleware>();
    });
```

## Common Mistakes

```csharp
// WRONG: Adding middleware in wrong order
app.UseAuthentication();   // Auth before CORS
app.UseCors("AllowAll");   // CORS preflight fails because auth rejects it

// CORRECT: CORS before authentication
app.UseCors("AllowAll");
app.UseAuthentication();
app.UseAuthorization();
```

```csharp
// WRONG: Calling next() multiple times
public async Task InvokeAsync(HttpContext context)
{
    await _next(context);
    await _next(context);  // Duplicate processing, corrupts response
}

// CORRECT: Call next() exactly once
public async Task InvokeAsync(HttpContext context)
{
    // Pre-processing
    await _next(context);
    // Post-processing
}
```

```csharp
// WRONG: Forgetting to call next() — request is silently short-circuited
public async Task InvokeAsync(HttpContext context)
{
    _logger.LogInformation("Request received");
    // Never calls _next — request never reaches endpoints
}

// CORRECT: Always call next unless intentionally short-circuiting
public async Task InvokeAsync(HttpContext context)
{
    _logger.LogInformation("Request received");
    await _next(context);
}
```

## Gotchas
- Middleware executes in the ORDER registered — UseAuthentication before UseAuthorization, UseCors before UseAuth
- `app.Use()` runs inline middleware; `app.UseMiddleware<T>()` uses DI-friendly class-based middleware
- Middleware registered with `app.Use()` does NOT get constructor DI — use `InvokeAsync` parameters instead
- `app.UseWhen` creates a branch only for matching requests; the branch reconnects to the main pipeline at the end
- `app.Map("/path", ...)` creates a completely separate pipeline branch that does NOT rejoin — use for truly isolated sub-apps
- Middleware singleton lifetime means injected scoped services must come from `InvokeAsync`, not the constructor
- `context.Response.HasStarted` — check before writing headers; writing after response started throws `InvalidOperationException`
- `app.UseExceptionHandler` only catches unhandled exceptions from downstream middleware; it must be first in the pipeline

## Related
- csharp/web/aspnet-basics.md
- csharp/stdlib/dependency-injection.md
- csharp/web/aspnet-auth.md
