---
id: "csharp-stdlib-linq-to-db"
title: "LINQ to Database: EF Core Query Translation, N+1, Projections"
language: "csharp"
category: "stdlib"
tags: ["csharp", "linq", "ef-core", "query", "n+1", "projection"]
version: "8.0+"
retrieval_hint: "csharp LINQ Entity Framework query translation N+1 Include ThenInclude projection Select"
last_verified: "2026-05-24"
confidence: "high"
---

# LINQ to Database: EF Core Query Translation, N+1, Projections

## When to Use
- Querying databases with Entity Framework Core
- Converting LINQ queries to efficient SQL
- Avoiding N+1 query problems with eager loading
- Projecting to DTOs for efficient data transfer

## Standard Pattern

```csharp
using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

// --- Models ---
public class User
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string Email { get; set; } = "";
    public DateTime CreatedAt { get; set; }

    public List<Order> Orders { get; set; } = new();
}

public class Order
{
    public int Id { get; set; }
    public DateTime OrderDate { get; set; }
    public decimal Total { get; set; }
    public int UserId { get; set; }
    public User User { get; set; } = null!;
    public List<OrderItem> Items { get; set; } = new();
}

public class OrderItem
{
    public int Id { get; set; }
    public string ProductName { get; set; } = "";
    public int Quantity { get; set; }
    public decimal Price { get; set; }
    public int OrderId { get; set; }
}

// --- DbContext ---
public class AppDbContext : DbContext
{
    public DbSet<User> Users => Set<User>();
    public DbSet<Order> Orders => Set<Order>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<User>(entity =>
        {
            entity.HasIndex(e => e.Email).IsUnique();
            entity.HasMany(e => e.Orders)
                  .WithOne(e => e.User)
                  .HasForeignKey(e => e.UserId);
        });
    }
}

// --- Query Patterns ---
public class UserRepository
{
    private readonly AppDbContext _db;

    public UserRepository(AppDbContext db)
    {
        _db = db;
    }

    // --- Eager Loading (Include) ---
    public async Task<List<User>> GetUsersWithOrdersAsync()
    {
        return await _db.Users
            .Include(u => u.Orders)
                .ThenInclude(o => o.Items)
            .ToListAsync();
        // Single SQL query with JOINs
    }

    // --- Projection (Select) — most efficient ---
    public async Task<List<UserDto>> GetUserDtosAsync()
    {
        return await _db.Users
            .Select(u => new UserDto
            {
                Id = u.Id,
                Name = u.Name,
                Email = u.Email,
                OrderCount = u.Orders.Count,
                TotalSpent = u.Orders.Sum(o => o.Total)
            })
            .ToListAsync();
        // Translates to SQL: SELECT, COUNT, SUM — single query
    }

    // --- Filtering and Sorting ---
    public async Task<List<User>> SearchUsersAsync(
        string? nameFilter,
        DateTime? createdAfter,
        string sortBy = "name",
        bool descending = false)
    {
        IQueryable<User> query = _db.Users;

        // Filter (where)
        if (!string.IsNullOrWhiteSpace(nameFilter))
            query = query.Where(u => u.Name.Contains(nameFilter));

        if (createdAfter.HasValue)
            query = query.Where(u => u.CreatedAt >= createdAfter.Value);

        // Sort
        query = sortBy.ToLower() switch
        {
            "email" => descending
                ? query.OrderByDescending(u => u.Email)
                : query.OrderBy(u => u.Email),
            "created" => descending
                ? query.OrderByDescending(u => u.CreatedAt)
                : query.OrderBy(u => u.CreatedAt),
            _ => descending
                ? query.OrderByDescending(u => u.Name)
                : query.OrderBy(u => u.Name)
        };

        return await query.ToListAsync();
    }

    // --- Pagination ---
    public async Task<PagedResult<User>> GetPagedUsersAsync(
        int page = 1, int pageSize = 20)
    {
        var query = _db.Users.AsNoTracking();

        var totalCount = await query.CountAsync();
        var items = await query
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync();

        return new PagedResult<User>
        {
            Items = items,
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize
        };
    }

    // --- Compiled Query (performance) ---
    private static readonly Func<AppDbContext, int, Task<User?>> GetUserById =
        EF.CompileAsyncQuery(
            (AppDbContext db, int id) =>
                db.Users.FirstOrDefault(u => u.Id == id));

    public async Task<User?> GetUserByIdCompiledAsync(int id)
    {
        return await GetUserById(_db, id);
        // Faster than regular query — compiled once
    }

    // --- Batch Operations ---
    public async Task DeleteInactiveUsersAsync(DateTime cutoff)
    {
        await _db.Users
            .Where(u => u.CreatedAt < cutoff && !u.Orders.Any())
            .ExecuteDeleteAsync();
        // EF Core 7+: translates to DELETE FROM Users WHERE ...
    }
}

// --- DTOs ---
public record UserDto
{
    public int Id { get; init; }
    public string Name { get; init; } = "";
    public string Email { get; init; } = "";
    public int OrderCount { get; init; }
    public decimal TotalSpent { get; init; }
}

public class PagedResult<T>
{
    public List<T> Items { get; init; } = new();
    public int TotalCount { get; init; }
    public int Page { get; init; }
    public int PageSize { get; init; }
    public int TotalPages => (int)Math.Ceiling(TotalCount / (double)PageSize);
}
```

## Common Mistakes

```csharp
// WRONG: N+1 query — iterating nav properties without Include
var users = await _db.Users.ToListAsync();
foreach (var user in users)
{
    Console.WriteLine(user.Orders.Count);  // One query per user!
}

// CORRECT: Eager load
var users = await _db.Users.Include(u => u.Orders).ToListAsync();
foreach (var user in users)
{
    Console.WriteLine(user.Orders.Count);  // No extra query
}


// WRONG: Client-side evaluation (expensive)
var users = await _db.Users
    .Where(u => u.Orders.Sum(o => o.Total) > 100)
    .ToListAsync();
// EF evaluates WHERE in memory — loads ALL users!

// CORRECT: Let EF translate to SQL
var users = await _db.Users
    .Where(u => u.Orders.Sum(o => o.Total) > 100)
    .ToListAsync();  // Same code! EF Core 3+ throws for untranslatable queries


// WRONG: Not using projections (Select) — loads unnecessary columns
var users = await _db.Users.ToListAsync();
var names = users.Select(u => u.Name).ToList();  // Loaded all columns from DB

// CORRECT: Project at query level
var names = await _db.Users.Select(u => u.Name).ToListAsync();  // Only Name column


// WRONG: Missing AsNoTracking for read-only queries
var users = await _db.Users.ToListAsync();  // Change tracking enabled — overhead!

// CORRECT: AsNoTracking for read-only
var users = await _db.Users.AsNoTracking().ToListAsync();
```

## Gotchas
- **Implicit transaction in SaveChanges**: EF Core wraps `SaveChanges` in a database transaction. For batch operations, this can hold locks longer than expected. Use `SaveChanges(false)` for explicit control.
- **Split query vs single query**: `Include` with multiple collections generates a single query with JOINs that can produce a Cartesian explosion. Use `AsSplitQuery()` to generate multiple queries for related collections.
- **Query cache plan explosion**: Each unique LINQ query generates a new SQL plan. Parameterize filter values (EF does this by default) to avoid cache bloat. Dynamic query composition (building `Where` clauses) can create many plans.
- **IQueryable vs IEnumerable**: `IQueryable` builds a SQL query — execution happens at the database. `IEnumerable` loads all data into memory and filters locally. Accidental `ToList()` before filtering is a common performance mistake.
- **Compiled queries**: `EF.CompileAsyncQuery` compiles the expression tree once. Use for hot paths (e.g., lookup by ID) where the query runs frequently. Not beneficial for one-off queries.
- **Enum conversion**: EF Core stores enums as integers by default. Use `HasConversion<string>()` to store as strings (more readable, slightly slower).
- **Value conversion**: Custom value converters run on every read/write. Ensure they're efficient — complex conversions in converters degrade query performance.

## Related
- csharp/stdlib/linq.md
- csharp/stdlib/linq-advanced.md
- csharp/db/entity-framework.md
