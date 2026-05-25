---
id: "security-sql-injection-prevention"
title: "SQL Injection Prevention"
language: "multi"
category: "security"
tags: ["sql-injection", "security", "parameterized-queries", "orm", "prepared-statements"]
version: "n/a"
retrieval_hint: "SQL injection prevention parameterized queries prepared statements ORM safety raw queries"
last_verified: "2026-05-24"
confidence: "high"
---

# SQL Injection Prevention

## When to Use
- Building any SQL query that incorporates user input
- Reviewing ORM usage for hidden injection vectors
- Setting up database access layers with proper parameterization
- Security auditing database interaction code

## Standard Pattern

```python
# === Python: Parameterized Queries ===

import psycopg2
from psycopg2 import sql

conn = psycopg2.connect(DATABASE_URL)

# CORRECT: Parameterized query (most important security practice)
cursor = conn.cursor()
cursor.execute("SELECT * FROM users WHERE email = %s AND active = %s", (email, True))
users = cursor.fetchall()

# CORRECT: Multiple parameters
cursor.execute(
    "INSERT INTO orders (user_id, product_id, quantity) VALUES (%s, %s, %s)",
    (user_id, product_id, quantity),
)

# CORRECT: Dynamic table/column names (can't use parameters for identifiers)
# Use psycopg2.sql for safe identifier composition
table_name = "users"  # From allowlist, NOT user input
query = sql.SQL("SELECT * FROM {} WHERE id = %s").format(sql.Identifier(table_name))
cursor.execute(query, (user_id,))

# CORRECT: SQLAlchemy ORM (parameterized by default)
from sqlalchemy import select
stmt = select(User).where(User.email == email)  # Safe
result = session.execute(stmt)

# CORRECT: SQLAlchemy Core
from sqlalchemy import table, column
users = table("users", column("email"), column("active"))
stmt = users.select().where(users.c.email == email)  # Safe
```

```java
// === Java: PreparedStatement ===

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;

// CORRECT: PreparedStatement with parameterized queries
public User findByEmail(Connection conn, String email) throws SQLException {
    String sql = "SELECT id, name, email FROM users WHERE email = ? AND active = ?";
    try (PreparedStatement stmt = conn.prepareStatement(sql)) {
        stmt.setString(1, email);
        stmt.setBoolean(2, true);
        ResultSet rs = stmt.executeQuery();
        if (rs.next()) {
            return new User(rs.getLong("id"), rs.getString("name"), rs.getString("email"));
        }
        return null;
    }
}

// CORRECT: JPA/Hibernate (parameterized by default)
@Query("SELECT u FROM User u WHERE u.email = :email AND u.active = :active")
Optional<User> findByEmail(@Param("email") String email, @Param("active") boolean active);

// CORRECT: JPA Criteria API for dynamic queries
CriteriaBuilder cb = entityManager.getCriteriaBuilder();
CriteriaQuery<User> query = cb.createQuery(User.class);
Root<User> user = query.from(User.class);
query.where(cb.equal(user.get("email"), email));  // Parameterized
```

```typescript
// === TypeScript/Node.js: Parameterized Queries ===

import { Pool } from "pg";

const pool = new Pool({ connectionString: DATABASE_URL });

// CORRECT: Parameterized with pg
const result = await pool.query(
    "SELECT * FROM users WHERE email = $1 AND active = $2",
    [email, true]
);

// CORRECT: Knex.js query builder
const users = await knex("users")
    .where({ email, active: true })
    .select("*");

// CORRECT: TypeORM
const user = await userRepository.findOne({
    where: { email, active: true },
});

// CORRECT: Prisma (parameterized by design)
const user = await prisma.user.findUnique({
    where: { email },
});
```

```go
// === Go: database/sql parameterized queries ===

import (
    "database/sql"
    _ "github.com/lib/pq"
)

// CORRECT: Parameterized query
func GetUserByEmail(db *sql.DB, email string) (*User, error) {
    var u User
    err := db.QueryRow(
        "SELECT id, name, email FROM users WHERE email = $1 AND active = $2",
        email, true,
    ).Scan(&u.ID, &u.Name, &u.Email)
    if err != nil {
        return nil, err
    }
    return &u, nil
}

// CORRECT: sqlx for convenience
type User struct {
    ID    int64  `db:"id"`
    Name  string `db:"name"`
    Email string `db:"email"`
}

func GetUserByEmail(db *sqlx.DB, email string) (*User, error) {
    var u User
    err := db.Get(&u, "SELECT * FROM users WHERE email = $1", email)
    return &u, err
}
```

## Common Mistakes

```python
# WRONG: String formatting in SQL (CLASSIC SQL INJECTION)
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
# Attacker: email = "' OR '1'='1' --" → returns ALL users

# CORRECT: Parameterized query
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
```

```python
# WRONG: String concatenation even with "safe" values
cursor.execute("SELECT * FROM " + table_name + " WHERE id = %s", (id,))
# If table_name comes from user input, you're vulnerable

# CORRECT: Allowlist table names or use sql.Identifier
ALLOWED_TABLES = {"users", "products", "orders"}
if table_name not in ALLOWED_TABLES:
    raise ValueError(f"Invalid table: {table_name}")
cursor.execute(sql.SQL("SELECT * FROM {} WHERE id = %s").format(
    sql.Identifier(table_name)
), (id,))
```

```python
# WRONG: ORM raw queries with string formatting
session.execute(text(f"SELECT * FROM users WHERE name LIKE '%{name}%'"))
# Still SQL injection even through ORM!

# CORRECT: Use bind parameters in raw queries
session.execute(text("SELECT * FROM users WHERE name LIKE :name"), {"name": f"%{name}%"})
```

```java
// WRONG: String concatenation in JDBC
String query = "SELECT * FROM users WHERE email = '" + email + "'";
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery(query);  // VULNERABLE

// CORRECT: PreparedStatement
PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE email = ?");
stmt.setString(1, email);
ResultSet rs = stmt.executeQuery();
```

```typescript
// WRONG: Template literals in SQL
await pool.query(`SELECT * FROM users WHERE email = '${email}'`);

// CORRECT: Parameterized
await pool.query("SELECT * FROM users WHERE email = $1", [email]);
```

## Gotchas
- ORMs are safe for basic queries but raw query methods (`text()`, `@Query(nativeQuery=true)`) bypass parameterization
- Parameter placeholders vary by database: PostgreSQL uses `$1`, MySQL uses `?`, SQLite uses `?` or `:name`
- Table names and column names CANNOT be parameterized — use allowlisting or library-safe identifier builders
- `LIKE` queries need parameterization too: `WHERE name LIKE %s` with `f"%{name}%"`
- Blind SQL injection doesn't show results directly — it uses timing or boolean responses
- Second-order SQL injection: data stored safely via parameters is later used unsafely in a different query
- `exec()` / `executemany()` in Python with `%` formatting is NOT the same as parameterized queries
- Stored procedures can still be vulnerable if they build dynamic SQL internally
- Input validation is NOT a substitute for parameterized queries — always use both

## Related
- security/web-security-basics.md
- security/owasp-top-10.md
- security/xss-prevention.md
- db/postgres/json-queries.md
