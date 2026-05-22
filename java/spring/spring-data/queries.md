---
id: "java-spring-data-queries"
title: "Spring Data JPA Queries"
language: "java"
category: "db"
subcategory: "orm"
tags: ["spring", "data", "jpa", "query", "jpql", "specification"]
version: "17+"
retrieval_hint: "Spring Data JPA query JPQL specification criteria"
last_verified: "2026-05-22"
confidence: "high"
---

# Spring Data JPA Queries

## When to Use
- Custom queries beyond method name derivation
- Dynamic query building
- Complex filtering with multiple optional parameters
- Projection queries

## Standard Pattern

```java
// Derived queries
public interface UserRepository extends JpaRepository<User, Long> {
    // Simple derived
    List<User> findByLastName(String lastName);
    List<User> findByAgeGreaterThan(int age);
    List<User> findByEmailContainingIgnoreCase(String email);
    
    // Multiple conditions
    List<User> findByLastNameAndAgeGreaterThan(String lastName, int age);
    
    // Ordering
    List<User> findByOrderByLastNameAscFirstNameAsc();
    
    // Top/Limit
    List<User> findTop5ByOrderByCreatedAtDesc();
    
    // JPQL query
    @Query("SELECT u FROM User u WHERE u.email LIKE %:domain% AND u.active = true")
    List<User> findActiveByEmailDomain(@Param("domain") String domain);
    
    // Projection
    @Query("SELECT new com.example.UserSummary(u.id, u.name, u.email) FROM User u WHERE u.active = true")
    List<UserSummary> findActiveUserSummaries();
    
    // Native query
    @Query(value = "SELECT * FROM users WHERE MATCH(name, email) AGAINST (:term)", nativeQuery = true)
    List<User> fullTextSearch(@Param("term") String term);
}

// Specification for dynamic queries
public class UserSpecifications {
    public static Specification<User> hasName(String name) {
        return (root, query, cb) -> 
            name == null ? null : cb.like(cb.lower(root.get("name")), "%" + name.toLowerCase() + "%");
    }
    
    public static Specification<User> hasEmail(String email) {
        return (root, query, cb) -> 
            email == null ? null : cb.equal(root.get("email"), email);
    }
    
    public static Specification<User> isActive() {
        return (root, query, cb) -> cb.equal(root.get("active"), true);
    }
}

// Usage with Specification
public interface UserRepository extends JpaRepository<User, Long>, JpaSpecificationExecutor<User> {}

// Dynamic query building
List<User> users = userRepository.findAll(
    Specification
        .where(UserSpecifications.hasName(searchName))
        .and(UserSpecifications.hasEmail(searchEmail))
        .and(UserSpecifications.isActive()),
    PageRequest.of(0, 10, Sort.by("createdAt").descending())
);
```

## Common Mistakes

```java
// WRONG: N+1 query problem
@Entity
public class User {
    @OneToMany(fetch = FetchType.LAZY)
    private List<Order> orders;
}

List<User> users = userRepository.findAll();
for (User user : users) {
    user.getOrders().size();  // Separate query for each user!
}

// CORRECT: Use JOIN FETCH
@Query("SELECT u FROM User u JOIN FETCH u.orders")
List<User> findAllWithOrders();

// WRONG: Using native query unnecessarily
@Query(value = "SELECT * FROM users WHERE name = :name", nativeQuery = true)
List<User> findByName(@Param("name") String name);

// CORRECT: Use JPQL for portability
@Query("SELECT u FROM User u WHERE u.name = :name")
List<User> findByName(@Param("name") String name);
```

## Gotchas
- Derived queries: `findBy` + property name + operator
- `IgnoreCase` suffix for case-insensitive comparison
- `Containing` for LIKE %value% queries
- `@Param` must match query parameter names
- `Specification` for dynamic queries with optional filters
- Use `JOIN FETCH` to avoid N+1 queries
- Projections reduce data transfer for list queries

## Related
- java/spring/spring-data/jpa-repositories.md
- java/spring/spring-data/transactions.md
