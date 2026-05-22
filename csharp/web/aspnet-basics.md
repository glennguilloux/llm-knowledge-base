---
id: "csharp-web-aspnet-basics"
title: "ASP.NET Core Web API Basics"
language: "csharp"
category: "web"
tags: ["csharp", "dotnet", "aspnet", "web-api", "minimal-api", "controller"]
version: ".NET 8+"
retrieval_hint: "C# ASP.NET Core Web API controller minimal API routing middleware"
last_verified: "2026-05-22"
confidence: "high"
---

# ASP.NET Core Web API Basics

## When to Use
- Building REST APIs
- Creating microservices
- Building web backends with .NET
- Serving JSON/XML responses

## Standard Pattern

```csharp
using Microsoft.AspNetCore.Mvc;

// === Minimal API (preferred for new projects) ===
var builder = WebApplication.CreateBuilder(args);
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();
app.UseSwagger();

// Simple endpoint
app.MapGet("/api/users", async (IUserRepo repo, CancellationToken ct) =>
{
    var users = await repo.GetAllAsync(ct);
    return Results.Ok(users);
});

app.MapGet("/api/users/{id:int}", async (int id, IUserRepo repo, CancellationToken ct) =>
{
    var user = await repo.GetByIdAsync(id, ct);
    return user is not null ? Results.Ok(user) : Results.NotFound();
});

app.MapPost("/api/users", async (CreateUserRequest req, IUserRepo repo, CancellationToken ct) =>
{
    var user = new User { Name = req.Name, Email = req.Email };
    await repo.AddAsync(user, ct);
    return Results.Created($"/api/users/{user.Id}", user);
});

app.MapPut("/api/users/{id:int}", async (int id, UpdateUserRequest req, IUserRepo repo, CancellationToken ct) =>
{
    var user = await repo.GetByIdAsync(id, ct);
    if (user is null) return Results.NotFound();
    user.Name = req.Name;
    await repo.UpdateAsync(user, ct);
    return Results.NoContent();
});

app.MapDelete("/api/users/{id:int}", async (int id, IUserRepo repo, CancellationToken ct) =>
{
    await repo.DeleteAsync(id, ct);
    return Results.NoContent();
});

// === Controller-based API ===
[ApiController]
[Route("api/[controller]")]
public class OrdersController : ControllerBase
{
    private readonly IOrderService _service;

    public OrdersController(IOrderService service) => _service = service;

    [HttpGet("{id:int}")]
    public async Task<ActionResult<OrderResponse>> GetOrder(int id, CancellationToken ct)
    {
        var order = await _service.GetAsync(id, ct);
        if (order is null) return NotFound();
        return Ok(order);
    }

    [HttpPost]
    public async Task<ActionResult<OrderResponse>> CreateOrder(
        [FromBody] CreateOrderRequest request, CancellationToken ct)
    {
        var order = await _service.CreateAsync(request, ct);
        return CreatedAtAction(nameof(GetOrder), new { id = order.Id }, order);
    }
}

// Model validation
public record CreateUserRequest
{
    [Required, MinLength(1), MaxLength(100)]
    public string Name { get; init; } = "";

    [Required, EmailAddress]
    public string Email { get; init; } = "";
}

// Middleware pipeline
app.UseHttpsRedirection();
app.UseCors("AllowFrontend");
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

// Global exception handler
app.UseExceptionHandler(error =>
{
    error.Run(async context =>
    {
        context.Response.StatusCode = 500;
        await context.Response.WriteAsJsonAsync(new { error = "Internal server error" });
    });
});

public interface IUserRepo { Task<List<User>> GetAllAsync(CancellationToken ct); Task<User?> GetByIdAsync(int id, CancellationToken ct); Task AddAsync(User user, CancellationToken ct); Task UpdateAsync(User user, CancellationToken ct); Task DeleteAsync(int id, CancellationToken ct); }
public interface IOrderService { Task<OrderResponse?> GetAsync(int id, CancellationToken ct); Task<OrderResponse> CreateAsync(CreateOrderRequest req, CancellationToken ct); }
public class User { public int Id { get; set; } public string Name { get; set; } = ""; public string Email { get; set; } = ""; }
public record UpdateUserRequest(string Name);
public record CreateOrderRequest(int UserId, decimal Total);
public record OrderResponse(int Id, int UserId, decimal Total);
public interface IOrderService { }
```

## Common Mistakes

```csharp
// WRONG: No input validation
app.MapPost("/api/users", async (dynamic body, IUserRepo repo) =>
{
    var name = (string)body.name;  // Runtime error if missing
    // ...
});

// CORRECT: Use strongly-typed models with validation
app.MapPost("/api/users", async (CreateUserRequest req, IUserRepo repo) =>
{
    // Model validation is automatic with [ApiController]
});

// WRONG: Not using CancellationToken
[HttpGet("{id}")]
public async Task<ActionResult<User>> Get(int id)  // No cancellation support
{
    return await _repo.GetByIdAsync(id);
}

// CORRECT: Accept CancellationToken
[HttpGet("{id}")]
public async Task<ActionResult<User>> Get(int id, CancellationToken ct)
{
    return await _repo.GetByIdAsync(id, ct);
}

// WRONG: Returning raw exceptions to client
app.MapGet("/api/users/{id}", (int id) =>
{
    try { return Results.Ok(repo.Get(id)); }
    catch (Exception ex) { return Results.BadRequest(ex.Message); }  // Leaks internals
});

// CORRECT: Use global exception handler, return generic errors
// Configure UseExceptionHandler in middleware pipeline

// WRONG: Middleware in wrong order
app.UseAuthorization();  // Before Authentication — always fails
app.UseAuthentication();

// CORRECT: Authentication before Authorization
app.UseAuthentication();
app.UseAuthorization();
```

## Gotchas
- `[ApiController]` enables automatic model validation — invalid requests return 400 before action runs
- `ActionResult<T>` allows returning both `T` and `IActionResult` (NotFound, BadRequest, etc.)
- `CreatedAtAction` returns 201 with Location header — REST best practice for POST
- Minimal APIs are simpler; Controllers give more structure — choose based on project size
- Middleware order matters: Exception → Routing → CORS → Auth → Authorization → Endpoints
- `app.MapGet` etc. support parameter binding from route, query, body, and headers
- `IResult` return types (`Results.Ok`, `Results.NotFound`) are more efficient than `ActionResult` in minimal APIs
- Swagger is built-in with `AddEndpointsApiExplorer()` + `AddSwaggerGen()`
- Use `[FromQuery]`, `[FromBody]`, `[FromRoute]`, `[FromHeader]` to control binding source

## Related
- csharp/stdlib/dependency-injection.md
- csharp/stdlib/async-await.md
- csharp/testing/testing.md
