---
id: "java-spring-data-jpa-repositories"
title: "Spring Data JPA Repositories"
language: "java"
category: "db"
subcategory: "orm"
tags: ["spring", "data", "jpa", "repository", "database", "entity"]
version: "17+"
retrieval_hint: "Spring Data JPA repository database entity CRUD"
last_verified: "2026-05-22"
confidence: "high"
---

# Spring Data JPA Repositories

## When to Use
- Database access with Spring Boot
- CRUD operations on entities
- Query derivation from method names
- Pagination and sorting

## Standard Pattern

```java
// Entity
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(unique = true, nullable = false)
    private String email;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }

    // Getters and setters
}

// Repository interface
public interface UserRepository extends JpaRepository<User, Long> {
    // Derived queries
    Optional<User> findByEmail(String email);
    List<User> findByNameContainingIgnoreCase(String name);
    boolean existsByEmail(String email);
    long countByActiveTrue();

    // Custom JPQL query
    @Query("SELECT u FROM User u WHERE u.createdAt > :since")
    List<User> findRecentUsers(@Param("since") LocalDateTime since);

    // Native query
    @Query(value = "SELECT * FROM users WHERE email LIKE %:domain%", nativeQuery = true)
    List<User> findByEmailDomain(@Param("domain") String domain);

    // Modifying query
    @Modifying
    @Query("UPDATE User u SET u.active = false WHERE u.lastLogin < :date")
    int deactivateInactiveUsers(@Param("date") LocalDateTime date);
}

// Service
@Service
@Transactional
public class UserService {
    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public Page<User> findAll(int page, int size) {
        return userRepository.findAll(PageRequest.of(page, size, Sort.by("createdAt").descending()));
    }

    public User create(UserRequest request) {
        User user = new User();
        user.setName(request.name());
        user.setEmail(request.email());
        return userRepository.save(user);
    }
}
```

## Common Mistakes

```java
// WRONG: Using @Autowired for repository
@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;  // Field injection!
}

// CORRECT: Use constructor injection
@Service
public class UserService {
    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }
}

// WRONG: Not handling Optional
User user = userRepository.findById(id).get();  // NoSuchElementException!

// CORRECT: Handle Optional
User user = userRepository.findById(id)
    .orElseThrow(() -> new ResourceNotFoundException("User not found"));
```

## Gotchas
- `JpaRepository<Entity, ID>` provides `save()`, `findById()`, `findAll()`, `delete()`
- Method name queries: `findBy`, `countBy`, `existsBy`, `deleteBy`
- `@Query` for custom JPQL or native queries
- `@Modifying` required for UPDATE/DELETE queries
- `Pageable` for pagination, `Sort` for sorting
- `@Entity` must have `@Id` field
- Use `@GeneratedValue(strategy = IDENTITY)` for auto-increment

## Real-World Example

### Full Repository Layer: Custom Queries, Pagination, and Projections

```java
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(nullable = false)
    private String name;

    @Enumerated(EnumType.STRING)
    private UserStatus status = UserStatus.ACTIVE;

    @CreatedDate
    private Instant createdAt;

    // getters, setters
}

public enum UserStatus { ACTIVE, INACTIVE, SUSPENDED }

// Projection for list views (avoid loading full entities)
public interface UserSummary {
    Long getId();
    String getName();
    String getEmail();
}

public interface UserRepository extends JpaRepository<User, Long> {

    // Derived query
    Optional<User> findByEmail(String email);

    // Projection + pagination
    Page<UserSummary> findByStatus(UserStatus status, Pageable pageable);

    // Custom JPQL with join fetch
    @Query("SELECT u FROM User u LEFT JOIN FETCH u.orders WHERE u.id = :id")
    Optional<User> findByIdWithOrders(@Param("id") Long id);

    // Native query for complex aggregations
    @Query(value = """
        SELECT u.id, u.name, u.email, COUNT(o.id) as order_count
        FROM users u
        LEFT JOIN orders o ON o.user_id = u.id
        WHERE u.status = :status
        GROUP BY u.id, u.name, u.email
        HAVING COUNT(o.id) > :minOrders
        """, nativeQuery = true)
    List<UserOrderStats> findActiveUsersWithMinOrders(
        @Param("status") String status,
        @Param("minOrders") int minOrders
    );

    // Bulk update
    @Modifying
    @Query("UPDATE User u SET u.status = :status WHERE u.lastLogin < :cutoff")
    int deactivateInactiveUsers(
        @Param("status") UserStatus status,
        @Param("cutoff") Instant cutoff
    );
}

// Usage in service
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepo;

    public Page<UserSummary> listActiveUsers(int page, int size) {
        return userRepo.findByStatus(
            UserStatus.ACTIVE,
            PageRequest.of(page, size, Sort.by("createdAt").descending())
        );
    }
}
```

## Related
- java/spring/spring-data/queries.md
- java/spring/spring-data/transactions.md
- java/spring/boot-basics.md
