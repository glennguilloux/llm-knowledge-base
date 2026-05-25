---
id: "csharp-testing-integration"
title: "ASP.NET Core Integration Testing: WebApplicationFactory, Test Server"
language: "csharp"
category: "testing"
tags: ["csharp", "testing", "integration", "webapplicationfactory", "test-server"]
version: "8.0+"
retrieval_hint: "csharp aspnet core integration testing WebApplicationFactory test server in-memory database"
last_verified: "2026-05-24"
confidence: "high"
---

# ASP.NET Core Integration Testing: WebApplicationFactory, Test Server

## When to Use
- Testing ASP.NET Core endpoints end-to-end
- Verifying HTTP request/response behavior
- Testing with a real database (in-memory or test instance)
- Validating middleware and authentication

## Standard Pattern

```csharp
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Xunit;

// --- Custom WebApplicationFactory ---
public class CustomWebApplicationFactory<TProgram>
    : WebApplicationFactory<TProgram> where TProgram : class
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            // Remove the real DbContext registration
            var descriptor = services.SingleOrDefault(
                d => d.ServiceType == typeof(DbContextOptions<AppDbContext>));

            if (descriptor != null)
            {
                services.Remove(descriptor);
            }

            // Add in-memory database for testing
            services.AddDbContext<AppDbContext>(options =>
            {
                options.UseInMemoryDatabase("TestDb");
            });

            // Ensure the database is created
            var sp = services.BuildServiceProvider();
            using (var scope = sp.CreateScope())
            {
                var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
                db.Database.EnsureCreated();
                // Seed test data
                SeedTestData(db);
            }
        });

        builder.UseEnvironment("Testing");
    }

    private void SeedTestData(AppDbContext db)
    {
        db.Users.Add(new User { Id = 1, Name = "Alice", Email = "alice@test.com" });
        db.Users.Add(new User { Id = 2, Name = "Bob", Email = "bob@test.com" });
        db.SaveChanges();
    }
}

// --- Integration Test Class ---
public class UsersApiTests
    : IClassFixture<CustomWebApplicationFactory<Program>>
{
    private readonly HttpClient _client;
    private readonly CustomWebApplicationFactory<Program> _factory;

    public UsersApiTests(CustomWebApplicationFactory<Program> factory)
    {
        _factory = factory;
        _client = factory.CreateClient();
    }

    // --- Basic GET Test ---
    [Fact]
    public async Task GetUsers_ReturnsSuccess()
    {
        // Act
        var response = await _client.GetAsync("/api/users");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    // --- JSON Response Test ---
    [Fact]
    public async Task GetUsers_ReturnsExpectedUsers()
    {
        // Act
        var response = await _client.GetAsync("/api/users");
        var users = await response.Content.ReadFromJsonAsync<List<UserDto>>();

        // Assert
        Assert.NotNull(users);
        Assert.Equal(2, users.Count);
        Assert.Contains(users, u => u.Name == "Alice");
    }

    // --- POST Test ---
    [Fact]
    public async Task CreateUser_ReturnsCreated()
    {
        // Arrange
        var newUser = new CreateUserRequest
        {
            Name = "Charlie",
            Email = "charlie@test.com"
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/users", newUser);

        // Assert
        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        var created = await response.Content.ReadFromJsonAsync<UserDto>();
        Assert.NotNull(created);
        Assert.Equal("Charlie", created.Name);
    }

    // --- Authentication Test ---
    [Fact]
    public async Task GetProtectedEndpoint_WithoutAuth_ReturnsUnauthorized()
    {
        // Act
        var response = await _client.GetAsync("/api/admin/users");

        // Assert
        Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
    }

    // --- Authenticated Request Test ---
    [Fact]
    public async Task GetProtectedEndpoint_WithAuth_ReturnsOk()
    {
        // Arrange — create client with auth header
        var client = _factory.CreateClient();
        client.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("Bearer", "test-token");

        // Mock authentication in factory setup
        // (Add custom auth handler in ConfigureWebHost)

        // Act
        var response = await client.GetAsync("/api/admin/users");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    // --- Validation Test ---
    [Fact]
    public async Task CreateUser_InvalidEmail_ReturnsBadRequest()
    {
        // Arrange
        var invalidUser = new CreateUserRequest
        {
            Name = "Test",
            Email = "not-an-email"
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/users", invalidUser);

        // Assert
        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }

    // --- Response Content Type Test ---
    [Fact]
    public async Task GetUsers_ReturnsJsonContentType()
    {
        // Act
        var response = await _client.GetAsync("/api/users");

        // Assert
        Assert.Equal("application/json", response.Content.Headers.ContentType?.MediaType);
    }
}

// --- Testing with Authentication ---
// For endpoints requiring auth, use a custom auth handler:
public class TestAuthHandler : AuthenticationHandler<AuthenticationSchemeOptions>
{
    public const string AuthenticationScheme = "Test";
    public const string TestUserId = "test-user-123";

    public TestAuthHandler(
        IOptionsMonitor<AuthenticationSchemeOptions> options,
        ILoggerFactory logger,
        UrlEncoder encoder)
        : base(options, logger, encoder) { }

    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        var claims = new[]
        {
            new Claim(ClaimTypes.NameIdentifier, TestUserId),
            new Claim(ClaimTypes.Name, "Test User"),
            new Claim(ClaimTypes.Role, "Admin"),
        };

        var identity = new ClaimsIdentity(claims, AuthenticationScheme);
        var principal = new ClaimsPrincipal(identity);
        var ticket = new AuthenticationTicket(principal, AuthenticationScheme);

        return Task.FromResult(AuthenticateResult.Success(ticket));
    }
}

// Register in ConfigureWebHost:
// builder.ConfigureTestServices(services =>
// {
//     services.AddAuthentication(TestAuthHandler.AuthenticationScheme)
//         .AddScheme<AuthenticationSchemeOptions, TestAuthHandler>(
//             TestAuthHandler.AuthenticationScheme, null);
// });
```

## Common Mistakes

```csharp
// WRONG: Not isolating tests — sharing factory state between tests
private static readonly WebApplicationFactory<Program> _factory = new();  // Shared!

[Fact]
public async Task Test1()
{
    var client = _factory.CreateClient();
    // Modifies DB state...
}

[Fact]
public async Task Test2()
{
    var client = _factory.CreateClient();
    // Sees Test1's DB changes — flaky!
}

// CORRECT: Use IClassFixture for fresh factory per test class
public class MyTests : IClassFixture<CustomWebApplicationFactory<Program>>
{
    // Fresh factory per test class, optionally with fresh DB per test
}


// WRONG: Using real database in integration tests (slow, flaky)
services.AddDbContext<AppDbContext>(options =>
    options.UseSqlServer(connectionString));  // Slow, requires SQL Server

// CORRECT: Use in-memory database
services.AddDbContext<AppDbContext>(options =>
    options.UseInMemoryDatabase($"TestDb_{Guid.NewGuid()}"));  // Unique per test


// WRONG: Sharing mutable state between tests
public class UsersApiTests : IClassFixture<CustomWebApplicationFactory<Program>>
{
    private List<UserDto> _cachedUsers;  // Mutable shared state!

    [Fact]
    public async Task Test1()
    {
        _cachedUsers = await GetUsersAsync();
    }
}

// CORRECT: No shared mutable state
```

## Gotchas
- **Factory lifetime management**: `WebApplicationFactory` is designed to be shared across tests (via `IClassFixture`). Creating a new factory per test is expensive. Use `IClassFixture` for factory reuse and fresh `HttpClient` per test.
- **Database state between tests**: In-memory databases persist data across tests unless explicitly recreated. Use `EnsureDeleted()` + `EnsureCreated()` in test setup or a unique database name per test.
- **Authentication in test setup**: Mock authentication by registering a test auth handler in `ConfigureWebHost`. Don't try to generate real JWT tokens in tests — it's fragile and slow.
- **`WebApplicationFactory` vs `TestServer`**: `WebApplicationFactory` creates a `TestServer` internally. Use `WebApplicationFactory` (higher-level) for most cases. Use `TestServer` directly only when you need finer control.
- **Content root path**: By default, `WebApplicationFactory` looks for the content root in the test assembly's directory. For multi-project solutions, override `ConfigureWebHost` to set `.UseContentRoot()`.
- **Dispose cleanup**: Always dispose `HttpClient` instances. The factory handles disposal of the test server. Consider using `ITestOutputHelper` for debugging test output.
- **Service overrides**: Use `ConfigureTestServices` (not `ConfigureServices`) to override services after the startup class has registered them. `ConfigureServices` replaces registrations entirely.

## Related
- csharp/web/aspnet-basics.md
- csharp/db/entity-framework.md
- csharp/stdlib/logging.md
