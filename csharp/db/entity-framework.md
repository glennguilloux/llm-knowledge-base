---
id: "csharp-db-entity-framework"
title: "Entity Framework Core Patterns"
language: "csharp"
category: "db"
tags: ["csharp", "dotnet", "entity-framework", "ef-core", "orm", "database"]
version: ".NET 8+"
retrieval_hint: "C# Entity Framework Core DbContext LINQ migration querying"
last_verified: "2026-05-24"
confidence: "high"
---

# Entity Framework Core Patterns

## When to Use
- Data access in .NET applications
- ORM for relational databases (SQL Server, PostgreSQL, SQLite)
- Database migrations and schema management
- Querying data with LINQ

## Standard Pattern

```csharp
using Microsoft.EntityFrameworkCore;

// DbContext configuration
public class AppDbContext : DbContext
{
    public DbSet<User> Users => Set<User>();
    public DbSet<Order> Orders => Set<Order>();

    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<User>(entity =>
        {
            entity.HasKey(u => u.Id);
            entity.HasIndex(u => u.Email).IsUnique();
            entity.Property(u => u.Name).HasMaxLength(200).IsRequired();
            entity.HasMany(u => u.Orders)
                  .WithOne(o => o.User)
                  .HasForeignKey(o => o.UserId)
                  .OnDelete(DeleteBehavior.Cascade);
        });
    }
}

// Registration in Program.cs
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("Default")));

// Repository pattern (optional — many use DbContext directly)
public class UserRepository : IUserRepository
{
    private readonly AppDbContext _db;

    public UserRepository(AppDbContext db) => _db = db;

    public async Task<User?> GetByIdAsync(int id, CancellationToken ct) =>
        await _db.Users.FindAsync(new object[] { id }, ct);

    public async Task<List<User>> GetActiveUsersAsync(CancellationToken ct) =>
        await _db.Users
            .Where(u => u.IsActive)
            .OrderBy(u => u.Name)
            .AsNoTracking()  // Read-only — better performance
            .ToListAsync(ct);

    public async Task<User> CreateAsync(User user, CancellationToken ct)
    {
        _db.Users.Add(user);
        await _db.SaveChangesAsync(ct);
        return user;
    }

    public async Task UpdateAsync(User user, CancellationToken ct)
    {
        _db.Users.Update(user);
        await _db.SaveChangesAsync(ct);
    }

    public async Task DeleteAsync(int id, CancellationToken ct)
    {
        var user = await _db.Users.FindAsync(new object[] { id }, ct);
        if (user is not null)
        {
            _db.Users.Remove(user);
            await _db.SaveChangesAsync(ct);
        }
    }
}

// Eager loading with Include
var usersWithOrders = await _db.Users
    .Include(u => u.Orders)
    .ToListAsync(ct);

// Projections (select only needed columns)
var summaries = await _db.Users
    .Select(u => new { u.Id, u.Name, OrderCount = u.Orders.Count })
    .ToListAsync(ct);

// Transactions
await using var transaction = await _db.Database.BeginTransactionAsync(ct);
try
{
    var user = new User { Name = "Alice" };
    _db.Users.Add(user);
    await _db.SaveChangesAsync(ct);

    var order = new Order { UserId = user.Id, Total = 99.99m };
    _db.Orders.Add(order);
    await _db.SaveChangesAsync(ct);

    await transaction.CommitAsync(ct);
}
catch
{
    await transaction.RollbackAsync(ct);
    throw;
}

public class User
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string Email { get; set; } = "";
    public bool IsActive { get; set; } = true;
    public List<Order> Orders { get; set; } = new();
}

public class Order
{
    public int Id { get; set; }
    public int UserId { get; set; }
    public User User { get; set; } = null!;
    public decimal Total { get; set; }
}
```

## Common Mistakes

```csharp
// WRONG: N+1 query — iterating and lazy loading
var users = await _db.Users.ToListAsync(ct);
foreach (var user in users)
{
    var orders = user.Orders;  // Separate query per user!
}

// CORRECT: Eager loading with Include
var users = await _db.Users.Include(u => u.Orders).ToListAsync(ct);

// WRONG: Tracking entities you only read
var users = await _db.Users.Where(u => u.IsActive).ToListAsync(ct);  // Change tracking overhead

// CORRECT: AsNoTracking for read-only queries
var users = await _db.Users.Where(u => u.IsActive).AsNoTracking().ToListAsync(ct);

// WRONG: Calling SaveChanges in a loop
foreach (var item in items)
{
    _db.Items.Add(item);
    await _db.SaveChangesAsync(ct);  // N round trips
}

// CORRECT: Batch save
foreach (var item in items) _db.Items.Add(item);
await _db.SaveChangesAsync(ct);  // Single round trip

// WRONG: Using First() without OrderBy
var user = await _db.Users.FirstAsync(ct);  // Non-deterministic

// CORRECT: Always OrderBy before First
var user = await _db.Users.OrderBy(u => u.Id).FirstAsync(ct);

// WRONG: Ignoring concurrency conflicts
await _db.SaveChangesAsync(ct);  // Last write wins silently

// CORRECT: Handle concurrency with tokens
public class User
{
    [Timestamp]
    public byte[] RowVersion { get; set; } = null!;
}
// EF throws DbUpdateConcurrencyException on conflict
```

## Gotchas
- `FindAsync` checks the change tracker first — returns cached entity without DB query
- `AsNoTracking()` disables change tracking — faster for read-only queries, but don't update the returned entities
- `Include` generates JOINs — chain multiple `Include` calls for nested navigation properties
- `SaveChangesAsync` batches SQL — adding 100 entities generates 100 INSERTs in one round trip
- EF Core uses identity resolution — same entity ID returns same object instance in one context
- Migrations: `Add-Migration` generates, `Update-Database` applies — use in development
- `UseNpgsql` / `UseSqlServer` / `UseSqlite` configures the provider — must match connection string
- Lazy loading requires proxy package and virtual navigation properties — prefer eager loading
- `DbContext` is scoped by default — one per request in web apps
- Raw SQL: `_db.Users.FromSqlRaw("SELECT * FROM Users WHERE ...")` for complex queries

## Related
- csharp/stdlib/linq.md
- csharp/stdlib/dependency-injection.md
- csharp/testing/testing.md
