---
id: "csharp-testing-mocking"
title: "C# Mocking with Moq and NSubstitute"
language: "csharp"
category: "testing"
subcategory: "unit-testing"
tags: ["csharp", "mocking", "moq", "nsubstitute", "unit-testing", "dependency-injection"]
version: "latest"
retrieval_hint: "C# mocking Moq NSubstitute mock setup verification argument matcher interface"
last_verified: "2026-05-24"
confidence: "high"
---

# C# Mocking with Moq and NSubstitute

## When to Use
- Unit testing services that depend on interfaces (repositories, HTTP clients, loggers)
- Isolating business logic from infrastructure (database, file system, external APIs)
- Testing error scenarios that are difficult to reproduce with real dependencies
- Verifying specific method calls and argument patterns

## Standard Pattern

### Moq — Setup and Verification

```csharp
// --- Interfaces ---
public interface IUserRepository
{
    Task<User?> GetByIdAsync(int id);
    Task<IEnumerable<User>> GetAllAsync();
    Task<int> CreateAsync(User user);
    Task<bool> DeleteAsync(int id);
}

public interface IEmailService
{
    Task SendWelcomeEmailAsync(string email, string name);
}

// --- Service under test ---
public class UserService
{
    private readonly IUserRepository _repo;
    private readonly IEmailService _email;

    public UserService(IUserRepository repo, IEmailService email)
    {
        _repo = repo;
        _email = email;
    }

    public async Task<UserDto?> GetUserAsync(int id)
    {
        var user = await _repo.GetByIdAsync(id);
        return user is null ? null : new UserDto(user.Id, user.Name, user.Email);
    }

    public async Task<int> RegisterAsync(string name, string email)
    {
        if (string.IsNullOrWhiteSpace(name) || string.IsNullOrWhiteSpace(email))
            throw new ArgumentException("Name and email are required.");

        var user = new User { Name = name, Email = email };
        var id = await _repo.CreateAsync(user);
        await _email.SendWelcomeEmailAsync(email, name);
        return id;
    }
}

// --- Tests using Moq ---
public class UserServiceTests
{
    private readonly Mock<IUserRepository> _repoMock;
    private readonly Mock<IEmailService> _emailMock;
    private readonly UserService _sut;

    public UserServiceTests()
    {
        _repoMock = new Mock<IUserRepository>();
        _emailMock = new Mock<IEmailService>();
        _sut = new UserService(_repoMock.Object, _emailMock.Object);
    }

    [Fact]
    public async Task GetUserAsync_ReturnsDto_WhenUserExists()
    {
        var user = new User { Id = 1, Name = "Alice", Email = "alice@example.com" };
        _repoMock.Setup(r => r.GetByIdAsync(1)).ReturnsAsync(user);

        var result = await _sut.GetUserAsync(1);

        Assert.NotNull(result);
        Assert.Equal("Alice", result.Name);
        _repoMock.Verify(r => r.GetByIdAsync(1), Times.Once);
    }

    [Fact]
    public async Task GetUserAsync_ReturnsNull_WhenUserNotFound()
    {
        _repoMock.Setup(r => r.GetByIdAsync(It.IsAny<int>())).ReturnsAsync((User?)null);

        var result = await _sut.GetUserAsync(99);

        Assert.Null(result);
    }

    [Fact]
    public async Task RegisterAsync_CreatesUserAndSendsEmail()
    {
        _repoMock.Setup(r => r.CreateAsync(It.IsAny<User>())).ReturnsAsync(42);

        var id = await _sut.RegisterAsync("Bob", "bob@example.com");

        Assert.Equal(42, id);
        _repoMock.Verify(r => r.CreateAsync(It.Is<User>(
            u => u.Name == "Bob" && u.Email == "bob@example.com"
        )), Times.Once);
        _emailMock.Verify(e => e.SendWelcomeEmailAsync("bob@example.com", "Bob"), Times.Once);
    }

    [Fact]
    public async Task RegisterAsync_ThrowsOnEmptyName()
    {
        await Assert.ThrowsAsync<ArgumentException>(() => _sut.RegisterAsync("", "bob@example.com"));
        _repoMock.Verify(r => r.CreateAsync(It.IsAny<User>()), Times.Never);
        _emailMock.Verify(e => e.SendWelcomeEmailAsync(It.IsAny<string>(), It.IsAny<string>()), Times.Never);
    }
}
```

### NSubstitute — Cleaner Syntax

```csharp
// --- Same interfaces, tests with NSubstitute ---
public class UserServiceNsTests
{
    private readonly IUserRepository _repo;
    private readonly IEmailService _email;
    private readonly UserService _sut;

    public UserServiceNsTests()
    {
        _repo = Substitute.For<IUserRepository>();
        _email = Substitute.For<IEmailService>();
        _sut = new UserService(_repo, _email);
    }

    [Fact]
    public async Task GetUserAsync_ReturnsDto()
    {
        var user = new User { Id = 1, Name = "Alice", Email = "alice@example.com" };
        _repo.GetByIdAsync(1).Returns(user);

        var result = await _sut.GetUserAsync(1);

        Assert.Equal("Alice", result!.Name);
        await _repo.Received(1).GetByIdAsync(1);
    }

    [Fact]
    public async Task RegisterAsync_SendsEmail()
    {
        _repo.CreateAsync(Arg.Any<User>()).Returns(42);

        await _sut.RegisterAsync("Bob", "bob@example.com");

        await _email.Received(1).SendWelcomeEmailAsync("bob@example.com", "Bob");
    }

    [Fact]
    public async Task RegisterAsync_DoesNotEmailOnFailure()
    {
        _repo.CreateAsync(Arg.Any<User>().Returns(Task.FromException<int>(new DbException("fail")));

        await Assert.ThrowsAsync<DbException>(() => _sut.RegisterAsync("Bob", "bob@example.com"));

        await _email.DidNotReceive().SendWelcomeEmailAsync(Arg.Any<string>(), Arg.Any<string>());
    }
}
```

## Common Mistakes

```csharp
// WRONG: Not verifying that mocks were actually called — test passes silently
_repoMock.Setup(r => r.GetByIdAsync(1)).ReturnsAsync(user);
var result = await _sut.GetUserAsync(1);
Assert.NotNull(result);
// Forgot to verify — if the service skips the repo call, test still passes

// CORRECT: Verify the interaction happened
_repoMock.Setup(r => r.GetByIdAsync(1)).ReturnsAsync(user);
var result = await _sut.GetUserAsync(1);
Assert.NotNull(result);
_repoMock.Verify(r => r.GetByIdAsync(1), Times.Once);
```

```csharp
// WRONG: Setup with exact value when service uses different value
_repoMock.Setup(r => r.GetByIdAsync(1)).ReturnsAsync(user);
// Service calls GetByIdAsync(2) — setup doesn't match, returns null

// CORRECT: Use It.IsAny<T>() when the exact value doesn't matter
_repoMock.Setup(r => r.GetByIdAsync(It.IsAny<int>())).ReturnsAsync(user);
// Or use a specific matcher if value matters
_repoMock.Setup(r => r.GetByIdAsync(It.Is<int>(id => id > 0))).ReturnsAsync(user);
```

```csharp
// WRONG: Mocking too much — testing implementation details instead of behavior
_repoMock.Verify(r => r.GetByIdAsync(1), Times.Once);
_repoMock.Verify(r => SomeInternalMethod(), Times.Once);  // Internal to service
_emailMock.Verify(e => e.SendWelcomeEmailAsync(...), Times.Once);

// CORRECT: Verify behavior, not implementation
// Only verify public contract — what the service returns and side effects users care about
var result = await _sut.RegisterAsync("Bob", "bob@example.com");
Assert.Equal(42, result);
await _email.Received(1).SendWelcomeEmailAsync("bob@example.com", "Bob");
```

## Gotchas
- Moq's `Setup` is matched in reverse order — the LAST matching setup wins; place general setups before specific ones
- `It.IsAny<T>()` matches any value including null — if your code passes null unexpectedly, tests won't catch it unless you verify explicitly
- NSubstitute's `Arg.Any<T>()` cannot be used outside of a Received/Returns call — storing it in a variable throws at runtime
- Moq's `Callback` runs BEFORE `Returns` — useful for capturing arguments but the callback must complete before the return value is used
- Async methods need `ReturnsAsync()` not `Returns(Task.FromResult())` — both work in Moq, but `ReturnsAsync` is cleaner; NSubstitute handles this automatically
- `VerifyAll()` checks that EVERY setup was called — stricter than `Verify()` which only checks explicitly verified calls; use `VerifyAll()` when all setups are mandatory
- Default mock behavior returns null for reference types and default for value types — configure `MockBehavior.Strict` to fail on unexpected calls (useful for detecting accidental interactions)
- NSubstitute's `.Returns()` with async: `_repo.GetByIdAsync(1).Returns(Task.FromResult<User?>(null))` — or use `_repo.GetByIdAsync(1).Returns((User?)null)` with the NSubstitute.Extensions

## Related
- csharp/testing/testing.md
- java/testing/mockito-deep.md
