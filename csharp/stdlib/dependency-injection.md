---
id: "csharp-stdlib-dependency-injection"
title: "Dependency Injection in .NET"
language: "csharp"
category: "stdlib"
tags: ["csharp", "dotnet", "dependency-injection", "di", "ioc", "service-lifetime"]
version: ".NET 8+"
retrieval_hint: "C# dependency injection IServiceCollection AddSingleton AddTransient AddScoped"
last_verified: "2026-05-24"
confidence: "high"
---

# Dependency Injection in .NET

## When to Use
- Building loosely coupled, testable applications
- Managing object lifetimes (singleton, scoped, transient)
- Configuring services at application startup
- Swapping implementations without changing consumers

## Standard Pattern

```csharp
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;

// Service registration in Program.cs
var builder = WebApplication.CreateBuilder(args);

// Register services with appropriate lifetimes
builder.Services.AddSingleton<ICacheService, RedisCacheService>();     // One instance forever
builder.Services.AddScoped<IUserRepository, UserRepository>();          // One per request
builder.Services.AddTransient<IEmailService, SmtpEmailService>();      // New instance every time

// Options pattern for configuration
builder.Services.Configure<DatabaseOptions>(
    builder.Configuration.GetSection("Database"));

// Factory registration
builder.Services.AddSingleton<IClock>(sp => new SystemClock());

// Open generic registration
builder.Services.AddScoped(typeof(IRepository<>), typeof(Repository<>));

var app = builder.Build();

// Constructor injection (preferred)
public class UserService
{
    private readonly IUserRepository _repo;
    private readonly IEmailService _email;
    private readonly ILogger<UserService> _logger;

    public UserService(
        IUserRepository repo,
        IEmailService email,
        ILogger<UserService> logger)
    {
        _repo = repo;
        _email = email;
        _logger = logger;
    }

    public async Task CreateUserAsync(CreateUserRequest request, CancellationToken ct)
    {
        var user = new User { Name = request.Name, Email = request.Email };
        await _repo.AddAsync(user, ct);
        await _email.SendWelcomeEmailAsync(user.Email, ct);
        _logger.LogInformation("Created user {UserId}", user.Id);
    }
}

// Options pattern usage
public class DatabaseOptions
{
    public string ConnectionString { get; set; } = "";
    public int CommandTimeout { get; set; } = 30;
}

public class UserRepository : IUserRepository
{
    private readonly DatabaseOptions _options;

    public UserRepository(IOptions<DatabaseOptions> options)
    {
        _options = options.Value;
    }
}

// Keyed services (.NET 8+)
builder.Services.AddKeyedSingleton<IPaymentProcessor>("stripe", new StripeProcessor());
builder.Services.AddKeyedSingleton<IPaymentProcessor>("paypal", new PayPalProcessor());

public class OrderService([FromKeyedServices("stripe")] IPaymentProcessor processor)
{
}

public interface IUserRepository { Task AddAsync(User user, CancellationToken ct); }
public class User { public int Id { get; set; } public string Name { get; set; } = ""; public string Email { get; set; } = ""; }
public class CreateUserRequest { public string Name { get; set; } = ""; public string Email { get; set; } = ""; }
public interface ICacheService { }
public class RedisCacheService : ICacheService { }
public interface IEmailService { Task SendWelcomeEmailAsync(string email, CancellationToken ct); }
public class SmtpEmailService : IEmailService { public Task SendWelcomeEmailAsync(string email, CancellationToken ct) => Task.CompletedTask; }
public interface IPaymentProcessor { }
public class StripeProcessor : IPaymentProcessor { }
public class PayPalProcessor : IPaymentProcessor { }
public interface IRepository<T> { }
public class Repository<T> : IRepository<T> { }
public interface IClock { }
public class SystemClock : IClock { }
```

## Common Mistakes

```csharp
// WRONG: Capturing scoped service in singleton
builder.Services.AddSingleton<BackgroundService>(sp =>
{
    var repo = sp.GetRequiredService<IUserRepository>();  // Scoped in singleton!
    return new BackgroundService(repo);  // Dies after first request scope ends
});

// CORRECT: Create scope manually in singleton
builder.Services.AddSingleton<BackgroundService>(sp =>
{
    return new BackgroundService(sp);
});

public class BackgroundService
{
    private readonly IServiceProvider _sp;
    public BackgroundService(IServiceProvider sp) { _sp = sp; }

    public async Task ExecuteAsync()
    {
        using var scope = _sp.CreateScope();
        var repo = scope.ServiceProvider.GetRequiredService<IUserRepository>();
        // Use repo within this scope
    }
}

// WRONG: Service Locator anti-pattern
public class UserService
{
    public async Task CreateUserAsync()
    {
        var repo = _serviceProvider.GetRequiredService<IUserRepository>();  // Hidden dependency
    }
}

// CORRECT: Constructor injection
public class UserService
{
    private readonly IUserRepository _repo;
    public UserService(IUserRepository repo) { _repo = repo; }
}

// WRONG: Resolving IDisposable from root provider
var service = sp.GetRequiredService<IMyDisposable>();  // Never disposed

// CORRECT: Use a scope
using var scope = sp.CreateScope();
var service = scope.ServiceProvider.GetRequiredService<IMyDisposable>();
// Disposed when scope is disposed

// WRONG: Registering implementation as both interface and concrete
builder.Services.AddSingleton<RedisCacheService>();
builder.Services.AddSingleton<ICacheService, RedisCacheService>();
// Injecting RedisCacheService vs ICacheService gives different instances

// CORRECT: Register once, as the abstraction
builder.Services.AddSingleton<ICacheService, RedisCacheService>();
```

## Gotchas
- `Transient` creates a new instance every time — avoid heavy constructors
- `Scoped` is per-request in web apps, per-scope in other apps
- `Singleton` lives for the application lifetime — must be thread-safe
- Never inject a shorter-lived service into a longer-lived one (captive dependency)
- `IServiceProvider` is itself a singleton — injecting it is the service locator pattern
- `IOptions<T>` is singleton and reads config once; `IOptionsSnapshot<T>` is scoped and re-reads per request
- `IOptionsMonitor<T>` is singleton with change notifications
- Always register abstractions (interfaces), not concrete types, for testability
- `AddSingleton<T>(instance)` uses the provided instance — be careful with mutable state
- `IHttpClientFactory` should be used instead of `new HttpClient()` for proper lifetime management

## Related
- csharp/stdlib/async-await.md
- csharp/web/aspnet-basics.md
- csharp/testing/testing.md
