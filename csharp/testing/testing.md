---
id: "csharp-testing-basics"
title: "Testing in .NET with xUnit"
language: "csharp"
category: "testing"
tags: ["csharp", "dotnet", "xunit", "testing", "mock", "moq", "integration"]
version: ".NET 8+"
retrieval_hint: "C# xUnit test Fact Theory Moq mock integration WebApplicationFactory"
last_verified: "2026-05-24"
confidence: "high"
---

# Testing in .NET with xUnit

## When to Use
- Unit testing business logic
- Integration testing API endpoints
- Mocking dependencies in tests
- Test-driven development

## Standard Pattern

```csharp
using Xunit;
using Moq;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;

// Basic unit test
public class UserServiceTests
{
    [Fact]
    public async Task CreateUser_ValidInput_ReturnsUser()
    {
        // Arrange
        var repoMock = new Mock<IUserRepository>();
        repoMock.Setup(r => r.AddAsync(It.IsAny<User>(), It.IsAny<CancellationToken>()))
                .ReturnsAsync((User u, CancellationToken _) => u);
        var service = new UserService(repoMock.Object);

        // Act
        var result = await service.CreateAsync(new CreateUserRequest("Alice", "alice@test.com"));

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Alice", result.Name);
        repoMock.Verify(r => r.AddAsync(It.IsAny<User>(), It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task GetUser_NotFound_ThrowsNotFoundException()
    {
        var repoMock = new Mock<IUserRepository>();
        repoMock.Setup(r => r.GetByIdAsync(99, It.IsAny<CancellationToken>()))
                .ReturnsAsync((User?)null);
        var service = new UserService(repoMock.Object);

        await Assert.ThrowsAsync<NotFoundException>(() => service.GetAsync(99));
    }
}

// Parameterized tests with [Theory]
public class CalculatorTests
{
    [Theory]
    [InlineData(2, 3, 5)]
    [InlineData(-1, 1, 0)]
    [InlineData(0, 0, 0)]
    public void Add_ReturnsCorrectSum(int a, int b, int expected)
    {
        Assert.Equal(expected, Calculator.Add(a, b));
    }

    [Theory]
    [MemberData(nameof(DivideTestData))]
    public void Divide_ReturnsCorrectResult(decimal a, decimal b, decimal expected)
    {
        Assert.Equal(expected, Calculator.Divide(a, b), 2);
    }

    public static IEnumerable<object[]> DivideTestData => new[]
    {
        new object[] { 10m, 3m, 3.33m },
        new object[] { 7m, 2m, 3.5m },
    };
}

// Integration test with WebApplicationFactory
public class UsersApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public UsersApiTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureServices(services =>
            {
                // Replace real DB with in-memory
                services.RemoveAll<DbContextOptions<AppDbContext>>();
                services.AddDbContext<AppDbContext>(o => o.UseInMemoryDatabase("TestDb"));
            });
        }).CreateClient();
    }

    [Fact]
    public async Task GetUsers_ReturnsOk()
    {
        var response = await _client.GetAsync("/api/users");
        response.EnsureSuccessStatusCode();
        var users = await response.Content.ReadFromJsonAsync<List<User>>();
        Assert.NotNull(users);
    }

    [Fact]
    public async Task CreateUser_ValidRequest_ReturnsCreated()
    {
        var request = new { Name = "Bob", Email = "bob@test.com" };
        var response = await _client.PostAsJsonAsync("/api/users", request);
        Assert.Equal(System.Net.HttpStatusCode.Created, response.StatusCode);
    }
}

public static class Calculator { public static int Add(int a, int b) => a + b; public static decimal Divide(decimal a, decimal b) => a / b; }
public class NotFoundException : Exception { }
public class UserService { public UserService(IUserRepository repo) { } public Task<User> CreateAsync(CreateUserRequest r) => Task.FromResult(new User { Name = r.Name }); public Task<User> GetAsync(int id) => throw new NotFoundException(); }
public record CreateUserRequest(string Name, string Email);
public interface IUserRepository { Task<User> AddAsync(User u, CancellationToken ct); Task<User?> GetByIdAsync(int id, CancellationToken ct); }
```

## Common Mistakes

```csharp
// WRONG: Testing implementation details
var service = new UserService(repo);
Assert.Equal(3, service._internalCounter);  // Breaks on refactor

// CORRECT: Test behavior, not implementation
var result = await service.CreateAsync(request);
Assert.Equal("Alice", result.Name);

// WRONG: Tests depend on each other
public class OrderTests
{
    private static int _orderId;
    [Fact]
    public void CreateOrder() { _orderId = 1; }
    [Fact]
    public void GetOrder() { var order = GetById(_orderId); }  // Fails if run first
}

// CORRECT: Each test is independent
public class OrderTests
{
    [Fact]
    public void CreateOrder() { /* self-contained */ }
    [Fact]
    public void GetOrder() { /* creates own test data */ }
}

// WRONG: Over-mocking (testing the mock, not the code)
var repoMock = new Mock<IUserRepository>();
repoMock.Setup(r => r.GetByIdAsync(1, It.IsAny<CancellationToken>()))
        .ReturnsAsync(new User { Id = 1, Name = "Alice" });
// If UserService just passes through to repo, you're testing nothing

// CORRECT: Mock external dependencies, test real logic

// WRONG: No assertions
[Fact]
public void ProcessOrder()
{
    var result = service.Process(order);  // No Assert — always passes
}

// CORRECT: Assert on expected behavior
[Fact]
public void ProcessOrder_SetsStatusToCompleted()
{
    var result = service.Process(order);
    Assert.Equal(OrderStatus.Completed, result.Status);
}
```

## Gotchas
- `IClassFixture<T>` shares a fixture (e.g., `WebApplicationFactory`) across all tests in a class
- `WebApplicationFactory<Program>` spins up the full app in-memory — use for integration tests
- `Moq` creates proxy objects — `It.IsAny<T>()` matches any argument
- `Verify` checks that a mock method was called; `Setup` defines what it returns
- xUnit runs tests in parallel by default — use `Collection` to serialize
- `IAsyncLifetime` for async setup/teardown (e.g., database seeding)
- `Assert.Throws<T>` for expected exceptions; `Assert.ThrowsAsync<T>` for async
- In-memory database (`UseInMemoryDatabase`) is NOT relational — no foreign key enforcement
- `WebApplicationFactory.WithWebHostBuilder` overrides services for testing
- Use `IClassFixture` for expensive setup (HTTP client, database); constructor for cheap setup

## Related
- csharp/web/aspnet-basics.md
- csharp/stdlib/dependency-injection.md
- csharp/db/entity-framework.md
