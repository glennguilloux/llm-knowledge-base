---
id: "csharp-minimal-api"
title: "Minimal APIs: .NET 6+ Endpoints, Filters, OpenAPI"
language: "csharp"
category: "web"
tags: ["csharp", "minimal-api", "aspnet", "web-api", "endpoints", "openapi"]
version: "n/a"
retrieval_hint: "csharp minimal API .NET 6 7 8 endpoints routing filters OpenAPI Swagger"
last_verified: "2026-05-24"
confidence: "high"
---

# Minimal APIs: .NET 6+ Endpoints, Filters, OpenAPI

## When to Use
- Building lightweight HTTP APIs without controllers
- Microservices and small web applications
- Prototyping and rapid development
- APIs with simple request/response patterns

## Standard Pattern

```csharp
// === Program.cs (Minimal API structure) ===

using Microsoft.OpenApi.Models;

var builder = WebApplication.CreateBuilder(args);

// Register services
builder.Services.AddScoped<IUserService, UserService>();
builder.Services.AddDbContext<AppDbContext>();

// OpenAPI
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo
    {
        Title = "My API",
        Version = "v1"
    });
});

var app = builder.Build();

app.UseSwagger();
app.UseSwaggerUI();

// === Route Groups ===

var users = app.MapGroup("/api/users")
    .WithTags("Users");

var admin = app.MapGroup("/api/admin")
    .RequireAuthorization("AdminPolicy");


// === CRUD Endpoints ===

// GET all
users.MapGet("/", async (IUserService service) =>
{
    var users = await service.GetAllAsync();
    return Results.Ok(users);
})
.WithName("GetUsers")
.WithOpenApi();

// GET by ID
users.MapGet("/{id:int}", async (int id, IUserService service) =>
{
    var user = await service.GetByIdAsync(id);
    return user is not null ? Results.Ok(user) : Results.NotFound();
})
.WithName("GetUserById");

// POST create
users.MapPost("/", async (CreateUserRequest request, IUserService service) =>
{
    var user = await service.CreateAsync(request);
    return Results.Created($"/api/users/{user.Id}", user);
})
.WithName("CreateUser")
.WithValidation();  // Built-in validation


// PUT update
users.MapPut("/{id:int}", async (int id, UpdateUserRequest request,
    IUserService service) =>
{
    var user = await service.UpdateAsync(id, request);
    return user is not null ? Results.Ok(user) : Results.NotFound();
})
.WithName("UpdateUser");

// DELETE
users.MapDelete("/{id:int}", async (int id, IUserService service) =>
{
    await service.DeleteAsync(id);
    return Results.NoContent();
})
.WithName("DeleteUser");


// === Filters ===

// Endpoint-specific filter
users.MapPost("/", async (User user) =>
{
    // Handler...
})
.AddFilter(async (context, next) =>
{
    // Before
    var logger = context.HttpContext.RequestServices
        .GetRequiredService<ILogger<Program>>();
    logger.LogInformation("Creating user...");

    var result = await next(context);

    // After
    logger.LogInformation("User created successfully");
    return result;
});


// === Parameter Binding ===

// From route
// GET /api/users/42 → id = 42
users.MapGet("/{id:int}", (int id) => { });

// From query string
// GET /api/users?page=1&size=10
users.MapGet("/", (int page = 1, int size = 20) => { });

// From body (POST/PUT)
users.MapPost("/", (CreateUserRequest request) => { });

// From header
users.MapGet("/", ([FromHeader] string authorization) => { });

// From service (DI)
users.MapGet("/", (IUserService service) => { });

// Custom binding (from multiple sources)
users.MapGet("/", (HttpContext context, HttpRequest request) => { });


// === Error Handling ===

app.UseExceptionHandler(exceptionHandlerApp =>
{
    exceptionHandlerApp.Run(async context =>
    {
        context.Response.StatusCode = StatusCodes.Status500InternalServerError;
        context.Response.ContentType = "application/json";

        var error = new { message = "An error occurred" };
        await context.Response.WriteAsJsonAsync(error);
    });
});


// === Validation (FluentValidation) ===

public class CreateUserRequest
{
    public string Name { get; set; } = "";
    public string Email { get; set; } = "";
}

public class CreateUserValidator : AbstractValidator<CreateUserRequest>
{
    public CreateUserValidator()
    {
        RuleFor(x => x.Name).NotEmpty().MaximumLength(100);
        RuleFor(x => x.Email).NotEmpty().EmailAddress();
    }
}

// Register: builder.Services.AddValidatorsFromAssemblyContaining<Program>();


app.Run();
```

## Common Mistakes

```csharp
// WRONG: No async/await on database calls (sync over async)
app.MapGet("/users", (AppDbContext db) =>
{
    return db.Users.ToList();  // Blocks thread!
});

// CORRECT: Use async
app.MapGet("/users", async (AppDbContext db) =>
{
    return await db.Users.ToListAsync();
});


// WRONG: Stringly-typed routes (no type safety)
app.MapGet("/users/{id}", (string id) => { });  // id is string!

// CORRECT: Use typed route parameters
app.MapGet("/users/{id:int}", (int id) => { });


// WRONG: Not grouping related endpoints
app.MapGet("/api/users", ...);
app.MapPost("/api/users", ...);
app.MapGet("/api/users/{id}", ...);  // Duplicated path prefixes

// CORRECT: Use route groups
var users = app.MapGroup("/api/users");
users.MapGet("/", ...);
users.MapPost("/", ...);
users.MapGet("/{id}", ...);


// WRONG: Returning anonymous types (no OpenAPI schema)
app.MapGet("/users", () => Results.Ok(new { id = 1, name = "Alice" }));

// CORRECT: Use typed response
app.MapGet("/users", () =>
{
    var user = new UserResponse { Id = 1, Name = "Alice" };
    return Results.Ok(user);
});


// WRONG: No OpenAPI metadata (poor Swagger output)
app.MapGet("/users", async (AppDbContext db) =>
{
    return await db.Users.ToListAsync();
});
// No .WithName(), no .WithOpenApi() — confusing Swagger

// CORRECT: Add metadata
app.MapGet("/users", async (AppDbContext db) => { ... })
    .WithName("GetUsers")
    .WithOpenApi();
```

## Gotchas
- **OpenAPI operation IDs**: `WithName()` sets the OpenAPI operationId. Without it, Swagger generates names like `GetUsers1`, `GetUsers2` — confusing for code generation tools. Always set unique names.
- **Request delegate caching**: Minimal API handlers are compiled and cached. First request may be slow (JIT compilation). For cold-start-sensitive apps, use AOT compilation or pre-warm with HTTP calls.
- **DI scope per request**: Scoped services (DbContext, scoped repositories) work correctly in minimal APIs — each HTTP request gets a new scope. Singleton services are shared across all requests.
- **Form file uploads**: Use `IFormFile` parameter type for file uploads. Enable multipart in the endpoint: `.Accepts<IFormFile>("multipart/form-data")`. Max file size defaults to 30MB — configure with `builder.WebHost.ConfigureKestrel(...)`.
- **Rate limiting**: .NET 7+ has built-in rate limiting: `builder.Services.AddRateLimiter(...)` and `app.UseRateLimiter()`. Configure per-endpoint policies for different API tiers.
- **AOT compilation**: .NET 8 minimal APIs support Native AOT for fast startup and small binaries. Not all ASP.NET features are compatible with AOT — check the AOT compatibility matrix before adopting for production.
- **Minimal API vs Controllers**: Controllers provide better organization for large APIs (20+ endpoints), better testability with `WebApplicationFactory`, and familiar patterns for team members. Minimal APIs excel for small services (5-10 endpoints) and prototypes.

## Related
- csharp/web/aspnet-basics.md
- csharp/web/aspnet-middleware.md
- csharp/web/aspnet-auth.md
