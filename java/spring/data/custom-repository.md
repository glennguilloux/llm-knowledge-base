---
id: "java-spring-data-custom-repository"
title: "Spring Data JPA Custom Repository Implementations"
language: "java"
category: "db"
subcategory: "orm"
tags: ["spring", "data", "jpa", "repository", "custom", "specification", "projection"]
version: "17+"
retrieval_hint: "Spring Data JPA custom repository Specification Projection DTO criteria"
last_verified: "2026-05-22"
confidence: "high"
---

# Spring Data JPA Custom Repository Implementations

## When to Use
- Complex queries that don't fit Spring Data's derived query methods
- Dynamic filtering with multiple optional parameters
- Returning DTOs instead of full entities (projections)
- Custom logic that needs EntityManager access

## Standard Pattern

```java
// --- Custom repository interface ---
public interface UserRepositoryCustom {
    List<User> findByFilters(String name, String email, LocalDate createdAfter, Pageable pageable);
    List<UserDTO> findUsersAsDTO();
}

// --- Custom repository implementation ---
@Repository
public class UserRepositoryImpl implements UserRepositoryCustom {
    private final EntityManager em;

    public UserRepositoryImpl(EntityManager em) {
        this.em = em;
    }

    @Override
    public List<User> findByFilters(String name, String email, LocalDate createdAfter, Pageable pageable) {
        CriteriaBuilder cb = em.getCriteriaBuilder();
        CriteriaQuery<User> query = cb.createQuery(User.class);
        Root<User> root = query.from(User.class);

        List<Predicate> predicates = new ArrayList<>();
        if (name != null) {
            predicates.add(cb.like(cb.lower(root.get("name")), "%" + name.toLowerCase() + "%"));
        }
        if (email != null) {
            predicates.add(cb.equal(root.get("email"), email));
        }
        if (createdAfter != null) {
            predicates.add(cb.greaterThan(root.get("createdAt"), createdAfter.atStartOfDay()));
        }

        query.where(predicates.toArray(new Predicate[0]));
        query.orderBy(cb.desc(root.get("createdAt")));

        return em.createQuery(query)
            .setFirstResult((int) pageable.getOffset())
            .setMaxResults(pageable.getPageSize())
            .getResultList();
    }
}

// --- Main repository extends custom ---
public interface UserRepository extends JpaRepository<User, Long>, UserRepositoryCustom {
    // Standard Spring Data methods still work
    Optional<User> findByEmail(String email);
}

// --- Specifications (reusable query predicates) ---
public class UserSpecs {
    public static Specification<User> nameLike(String name) {
        return (root, query, cb) ->
            name == null ? null : cb.like(cb.lower(root.get("name")), "%" + name.toLowerCase() + "%");
    }

    public static Specification<User> createdAfter(LocalDate date) {
        return (root, query, cb) ->
            date == null ? null : cb.greaterThan(root.get("createdAt"), date.atStartOfDay());
    }

    public static Specification<User> hasRole(String role) {
        return (root, query, cb) ->
            role == null ? null : cb.equal(root.get("role"), role);
    }
}

// Using Specifications
public interface UserRepository extends JpaRepository<User, Long>, JpaSpecificationExecutor<User> {}

// In service:
List<User> users = userRepository.findAll(
    UserSpecs.nameLike("alice")
        .and(UserSpecs.createdAfter(LocalDate.of(2024, 1, 1)))
);

// --- Interface-based projections ---
public interface UserSummary {
    Long getId();
    String getName();
    String getEmail();
    // No setters needed — Spring Data creates proxy
}

public interface UserRepository extends JpaRepository<User, Long> {
    List<UserSummary> findByIsActiveTrue();  // Returns projection
}

// --- DTO projections with @Query ---
public interface UserRepository extends JpaRepository<User, Long> {
    @Query("SELECT new com.example.dto.UserDTO(u.id, u.name, u.email) FROM User u WHERE u.isActive = true")
    List<UserDTO> findActiveUsersAsDTO();
}
```

## Common Mistakes

```java
// WRONG: Building queries with string concatenation (SQL injection)
String jpql = "SELECT u FROM User u WHERE u.name = '" + name + "'";
em.createQuery(jpql);  // Vulnerable!

// CORRECT: Use parameterized queries
em.createQuery("SELECT u FROM User u WHERE u.name = :name")
    .setParameter("name", name);

// WRONG: Using findAll() with no pagination on large tables
List<User> users = userRepository.findAll();  // Loads millions of rows!

// CORRECT: Use Pageable
Page<User> users = userRepository.findAll(PageRequest.of(0, 20));

// WRONG: Custom implementation not in correct package
// UserRepositoryImpl must be in same package as UserRepository

// CORRECT: Follow naming convention: {RepositoryName}Impl

// WRONG: Specification returning null predicate (may cause issues)
public static Specification<User> nameLike(String name) {
    return (root, query, cb) -> cb.like(...);  // Applied even if name is null
}

// CORRECT: Return null for "no filter"
public static Specification<User> nameLike(String name) {
    return (root, query, cb) -> name == null ? null : cb.like(...);
}
```

## Gotchas
- Custom implementation class must be named `{RepositoryInterface}Impl` (suffix `Impl`)
- `Specification` predicates returning `null` are ignored — useful for optional filters
- Interface projections use lazy proxies — accessing unloaded properties triggers additional queries
- DTO projections via `@Query` require explicit constructor call: `new com.example.dto.UserDTO(...)`
- `JpaSpecificationExecutor` must be extended for `findAll(Specification)` support
- Custom implementations are automatically picked up by Spring Data — no extra config needed
- `CriteriaQuery` is type-safe; JPQL is string-based — use Criteria for dynamic queries
- `Pageable` in custom implementations must be applied manually (no auto-pagination)

## Related
- java/spring/spring-data/jpa-repositories.md
- java/spring/spring-data/queries.md
- java/spring/spring-data/transactions.md
