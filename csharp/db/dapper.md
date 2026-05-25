---
id: "csharp-dapper"
title: "Dapper: Micro-ORM for ADO.NET, Queries, Mapping, Performance"
language: "csharp"
category: "db"
tags: ["csharp", "dapper", "orm", "sql", "ado.net", "micro-orm"]
version: "n/a"
retrieval_hint: "csharp dapper micro-orm ADO.NET SQL queries mapping multi-mapping stored procedures"
last_verified: "2026-05-24"
confidence: "high"
---

# Dapper: Micro-ORM for ADO.NET, Queries, Mapping, Performance

## When to Use
- High-performance database access without full ORM overhead
- Mapping SQL query results to POCOs
- Executing stored procedures with minimal ceremony
- Complex queries where full ORMs (EF Core) add complexity

## Standard Pattern

```csharp
using System.Data;
using System.Data.SqlClient;
using Dapper;

// === Dependencies ===
// Install-Package Dapper
// Install-Package Microsoft.Data.SqlClient

// === Connection Setup ===

public class DatabaseService
{
    private readonly string _connectionString;

    public DatabaseService(string connectionString)
    {
        _connectionString = connectionString;
    }

    private IDbConnection CreateConnection()
        => new SqlConnection(_connectionString);


    // === Basic Queries ===

    public async Task<User?> GetUserByIdAsync(int id)
    {
        using var conn = CreateConnection();
        return await conn.QueryFirstOrDefaultAsync<User>(
            "SELECT * FROM Users WHERE Id = @Id",
            new { Id = id }
        );
    }

    public async Task<IEnumerable<User>> GetActiveUsersAsync()
    {
        using var conn = CreateConnection();
        return await conn.QueryAsync<User>(
            "SELECT * FROM Users WHERE IsActive = @Active",
            new { Active = true }
        );
    }


    // === Parameterized Queries ===

    public async Task<IEnumerable<User>> SearchUsersAsync(
        string nameFilter, string? role = null)
    {
        using var conn = CreateConnection();

        var sql = "SELECT * FROM Users WHERE Name LIKE @Name";
        var parameters = new DynamicParameters();
        parameters.Add("Name", $"%{nameFilter}%");

        if (role != null)
        {
            sql += " AND Role = @Role";
            parameters.Add("Role", role);
        }

        return await conn.QueryAsync<User>(sql, parameters);
    }


    // === Multi-Mapping (JOINs) ===

    public async Task<IEnumerable<Order>> GetOrdersWithUserAsync()
    {
        using var conn = CreateConnection();

        var sql = @"
            SELECT o.*, u.*
            FROM Orders o
            INNER JOIN Users u ON o.UserId = u.Id";

        return await conn.QueryAsync<Order, User, Order>(
            sql,
            (order, user) =>
            {
                order.User = user;
                return order;
            },
            splitOn: "Id"  // First column of User table
        );
    }


    // === Stored Procedures ===

    public async Task<IEnumerable<Order>> GetOrdersByDateRangeAsync(
        DateTime start, DateTime end)
    {
        using var conn = CreateConnection();

        return await conn.QueryAsync<Order>(
            "usp_GetOrdersByDateRange",
            new { StartDate = start, EndDate = end },
            commandType: CommandType.StoredProcedure
        );
    }


    // === Transactions ===

    public async Task TransferFundsAsync(
        int fromAccount, int toAccount, decimal amount)
    {
        using var conn = CreateConnection();
        conn.Open();

        using var transaction = conn.BeginTransaction();

        try
        {
            await conn.ExecuteAsync(
                "UPDATE Accounts SET Balance = Balance - @Amount WHERE Id = @From",
                new { Amount = amount, From = fromAccount },
                transaction: transaction
            );

            await conn.ExecuteAsync(
                "UPDATE Accounts SET Balance = Balance + @Amount WHERE Id = @To",
                new { Amount = amount, To = toAccount },
                transaction: transaction
            );

            transaction.Commit();
        }
        catch
        {
            transaction.Rollback();
            throw;
        }
    }


    // === Bulk Insert (Table-Valued Parameter) ===

    public async Task BulkInsertUsersAsync(IEnumerable<User> users)
    {
        using var conn = CreateConnection();
        await conn.ExecuteAsync(
            "INSERT INTO Users (Name, Email) VALUES (@Name, @Email)",
            users  // Dapper batches automatically
        );
    }


    // === Execute Scalar ===

    public async Task<int> GetUserCountAsync()
    {
        using var conn = CreateConnection();
        return await conn.ExecuteScalarAsync<int>(
            "SELECT COUNT(*) FROM Users"
        );
    }
}


// === Models ===

public class User
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string Email { get; set; } = "";
    public bool IsActive { get; set; }
}

public class Order
{
    public int Id { get; set; }
    public int UserId { get; set; }
    public decimal Total { get; set; }
    public User? User { get; set; }
}
```

## Common Mistakes

```csharp
// WRONG: SQL injection via string interpolation
var sql = $"SELECT * FROM Users WHERE Name = '{name}'";  // DANGER!
// name = "'; DROP TABLE Users; --"

// CORRECT: Always use parameterized queries
var sql = "SELECT * FROM Users WHERE Name = @Name";
var user = conn.QueryFirstOrDefault<User>(sql, new { Name = name });


// WRONG: Not disposing connections
var conn = new SqlConnection(connectionString);
var user = conn.QueryFirst<User>("SELECT * FROM Users");  // Connection leak!

// CORRECT: Use using
using var conn = new SqlConnection(connectionString);
var user = conn.QueryFirst<User>("SELECT * FROM Users");


// WRONG: Multiple result sets without QueryMultiple
var users = conn.Query<User>("SELECT * FROM Users");
var orders = conn.Query<Order>("SELECT * FROM Orders");
// Two round trips!

// CORRECT: Use QueryMultiple
using var multi = conn.QueryMultiple(@"
    SELECT * FROM Users;
    SELECT * FROM Orders;
");
var users = multi.Read<User>();
var orders = multi.Read<Order>();


// WRONG: Mapping private properties
class User
{
    private int Id { get; set; }  // Dapper won't set this
}

// CORRECT: Properties must be public with get/set
class User
{
    public int Id { get; set; }
}


// WRONG: SELECT * on large tables (unnecessary columns transferred)
var users = conn.Query<User>("SELECT * FROM Users");

// CORRECT: Select only needed columns
var users = conn.Query<User>("SELECT Id, Name, Email FROM Users");
```

## Gotchas
- **Connection must be open**: Dapper doesn't automatically open connections. Call `conn.Open()` explicitly or rely on Dapper's automatic open (it opens closed connections but doesn't close them if it opened them).
- **Column name mismatch**: Dapper maps by exact column name. If your SQL column is `user_name` and your property is `UserName`, use column aliases (`SELECT user_name AS UserName`) or add `[Column("user_name")]` attribute.
- **Query vs QueryAsync**: `Query<T>` blocks the thread during I/O. Always use `QueryAsync<T>` in async contexts. Mixing sync and async can cause thread pool starvation under load.
- **DynamicParameters order**: For stored procedures with named parameters, `DynamicParameters` preserves order by default. Explicitly name parameters for clarity and to avoid ordering bugs.
- **Multi-mapping splitOn**: The `splitOn` parameter defaults to `"Id"`. If your JOIN has multiple `Id` columns (e.g., `Orders.Id` and `Users.Id`), splitOn stops at the first `Id`. Use unique aliases: `SELECT o.Id AS OrderId, u.Id AS UserId`.
- **Bulk insert performance**: Dapper's `ExecuteAsync` with an `IEnumerable` sends individual INSERT statements. For >1000 rows, use `SqlBulkCopy` directly or table-valued parameters.
- **TransactionScope**: For distributed transactions spanning multiple databases, use `TransactionScope` (requires MSDTC). For single-database transactions, `BeginTransaction` is faster and more reliable.

## Related
- csharp/db/entity-framework.md
- csharp/stdlib/performance.md
- db/mysql/basics.md
