---
id: "csharp-stdlib-background-services"
title: ".NET Background Services and Worker Service"
language: "csharp"
category: "stdlib"
subcategory: "background-processing"
tags: ["csharp", "dotnet", "background", "worker", "hosted-service", "timer", "queue"]
version: "8.0+"
retrieval_hint: ".NET BackgroundService IHostedService Worker Service periodic timer queue processing"
last_verified: "2026-05-22"
confidence: "high"
---

# .NET Background Services and Worker Service

## When to Use
- Long-running background tasks: cleanup, polling, synchronization
- Queue-based processing: reading from queues and processing messages
- Scheduled jobs that run on a timer (periodic or cron-like)
- Offloading work from HTTP request handlers

## Standard Pattern

```csharp
// Simple periodic background service
public class HealthCheckService : BackgroundService
{
    private readonly ILogger<HealthCheckService> _logger;
    private readonly IServiceProvider _services;

    public HealthCheckService(ILogger<HealthCheckService> logger, IServiceProvider services)
    {
        _logger = logger;
        _services = services;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                using var scope = _services.CreateScope();
                var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
                var count = await db.Orders.CountAsync(o => o.Status == "Pending", stoppingToken);
                _logger.LogInformation("Pending orders: {Count}", count);
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                _logger.LogError(ex, "Health check failed");
            }

            await Task.Delay(TimeSpan.FromMinutes(5), stoppingToken);
        }
    }
}

// Registration
builder.Services.AddHostedService<HealthCheckService>();
```

## Queue-Based Background Processor

```csharp
// Thread-safe background queue
public interface IBackgroundQueue<T>
{
    ValueTask QueueAsync(T item);
    ValueTask<T> DequeueAsync(CancellationToken cancellationToken);
}

public class BackgroundQueue<T> : IBackgroundQueue<T>
{
    private readonly Channel<T> _channel = Channel.CreateUnbounded<T>();

    public ValueTask QueueAsync(T item) =>
        _channel.Writer.WriteAsync(item);

    public ValueTask<T> DequeueAsync(CancellationToken cancellationToken) =>
        _channel.Reader.ReadAsync(cancellationToken);
}

// Register queue
builder.Services.AddSingleton<IBackgroundQueue<EmailRequest>>(_ =>
    new BackgroundQueue<EmailRequest>());

// Queue processor service
public class EmailProcessorService : BackgroundService
{
    private readonly IBackgroundQueue<EmailRequest> _queue;
    private readonly IServiceProvider _services;
    private readonly ILogger<EmailProcessorService> _logger;

    public EmailProcessorService(
        IBackgroundQueue<EmailRequest> queue,
        IServiceProvider services,
        ILogger<EmailProcessorService> logger)
    {
        _queue = queue;
        _services = services;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await foreach (var request in _queue.DequeueAsync(stoppingToken))
        {
            try
            {
                using var scope = _services.CreateScope();
                var emailService = scope.ServiceProvider.GetRequiredService<IEmailService>();
                await emailService.SendAsync(request);
                _logger.LogInformation("Sent email to {To}", request.To);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to send email to {To}", request.To);
            }
        }
    }
}

// Enqueue from controllers
[HttpPost("send")]
public async Task<IActionResult> SendEmail(EmailRequest request)
{
    await _queue.QueueAsync(request);
    return Accepted();
}
```

## Graceful Shutdown

```csharp
// Program.cs — configure shutdown timeout
builder.Services.Configure<HostOptions>(options =>
{
    options.ShutdownTimeout = TimeSpan.FromSeconds(30);
});

// In ExecuteAsync — use stoppingToken for cooperative cancellation
protected override async Task ExecuteAsync(CancellationToken stoppingToken)
{
    // stoppingToken is triggered when the app is shutting down
    // Use it to stop processing gracefully

    while (!stoppingToken.IsCancellationRequested)
    {
        var item = await _queue.DequeueAsync(stoppingToken);
        await ProcessAsync(item, stoppingToken);
    }

    // Optional: cleanup logic after cancellation
    _logger.LogInformation("Background service stopped gracefully");
}

// Worker Service template (standalone process)
// dotnet new worker -name MyWorker
public class Worker : BackgroundService
{
    private readonly ILogger<Worker> _logger;

    public Worker(ILogger<Worker> logger) => _logger = logger;

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            _logger.LogInformation("Worker running at: {Time}", DateTimeOffset.Now);
            await Task.Delay(1000, stoppingToken);
        }
    }
}
```

## Common Mistakes

```csharp
// WRONG: Creating scoped services in a singleton background service
protected override async Task ExecuteAsync(CancellationToken stoppingToken)
{
    var db = _services.GetRequiredService<AppDbContext>();  // Leaked scope!
    while (!stoppingToken.IsCancellationRequested)
    {
        var items = await db.Orders.ToListAsync();  // DbContext tracks entities forever
    }
}

// CORRECT: Create a new scope per iteration
protected override async Task ExecuteAsync(CancellationToken stoppingToken)
{
    while (!stoppingToken.IsCancellationRequested)
    {
        using var scope = _services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var items = await db.Orders.ToListAsync(stoppingToken);
    }
}
```

```csharp
// WRONG: Ignoring stoppingToken — service won't shut down gracefully
protected override async Task ExecuteAsync(CancellationToken stoppingToken)
{
    while (true)  // Never checks cancellation
    {
        await DoWork();
        await Task.Delay(5000);  // Delays even during shutdown
    }
}

// CORRECT: Use stoppingToken for cooperative cancellation
protected override async Task ExecuteAsync(CancellationToken stoppingToken)
{
    while (!stoppingToken.IsCancellationRequested)
    {
        await DoWork(stoppingToken);
        await Task.Delay(5000, stoppingToken);  // Throws OperationCanceledException on shutdown
    }
}
```

```csharp
// WRONG: Swallowing OperationCanceledException as an error
catch (Exception ex)
{
    _logger.LogError(ex, "Error");  // Logs cancellation as error during shutdown
}

// CORRECT: Filter out cancellation
catch (Exception ex) when (ex is not OperationCanceledException)
{
    _logger.LogError(ex, "Error");
}
```

## Gotchas
- `BackgroundService.ExecuteAsync` runs once — if it returns, the service stops; use `while` loops for continuous work
- `Task.Delay(Timeout.Infinite, stoppingToken)` for services that only wake on external signals (not timers)
- Scoped services (DbContext, repositories) must be created with `CreateScope()` per unit of work — never inject `IOptionsSnapshot<T>` into singletons
- `StopAsync` is called during shutdown — override it for cleanup; `ExecuteAsync` cancellation token is triggered first
- Multiple `IHostedService` implementations run concurrently — startup order is registration order but NOT sequential
- The `Worker Service` template creates a standalone console app (no web server) — use for non-HTTP background processors
- `Channel<T>` is the recommended producer/consumer pattern; `ConcurrentQueue<T>` with polling wastes CPU
- `stoppingToken.IsCancellationRequested` should be checked inside long-running loops; `Task.Delay` with token handles it automatically

## Related
- csharp/stdlib/dependency-injection.md
- csharp/stdlib/configuration.md
- csharp/stdlib/async-await.md
