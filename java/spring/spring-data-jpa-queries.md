---
id: "java-spring-data-jpa-queries"
title: "Spring Data JPA Query Patterns"
language: "java"
category: "web"
subcategory: "data-jpa"
tags: ["spring", "spring-data", "jpa", "repository", "query", "projection", "pagination", "fetch-join", "n-plus-one"]
version: "17+"
retrieval_hint: "Spring Data JPA repository query projection pagination @Query derived methods entity graph N+1"
last_verified: "2026-06-20"
confidence: "medium"
---

# Spring Data JPA Query Patterns

## When to Use
- Building repository methods that need derived queries, explicit JPQL, or native SQL without hand-writing JDBC.
- Returning pageable result sets with stable sorting for API list endpoints.
- Reducing N+1 query problems with `join fetch`, `@EntityGraph`, or DTO projections.
- Keeping database-specific SQL isolated behind repository interfaces.

## Standard Pattern

```java
package com.example.catalog;

import jakarta.persistence.*;
import org.springframework.data.domain.*;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Entity
@Table(name = "users")
class User {
    @Id
    private Long id;

    @Column(nullable = false)
    private String email;

    @Enumerated(EnumType.STRING)
    private UserStatus status;

    private Instant createdAt;

    @OneToMany(mappedBy = "user", fetch = FetchType.LAZY)
    private List<Order> orders = List.of();

    // getters omitted for brevity
}

enum UserStatus { ACTIVE, DISABLED }

class Order {
    @Id
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    private User user;

    // getters omitted for brevity
}

interface UserEmailProjection {
    Long getId();
    String getEmail();
    UserStatus getStatus();
}

interface UserRepository extends JpaRepository<User, Long> {

    List<User> findByStatusOrderByCreatedAtDesc(UserStatus status);

    @Query("""
        select u
        from User u
        join fetch u.orders o
        where u.status = :status
        order by u.createdAt desc
        """)
    List<User> findActiveUsersWithOrders(@Param("status") UserStatus status);

    @Query("""
        select u.id as id, u.email as email, u.status as status
        from User u
        where u.email like concat(:prefix, '%')
        """)
    List<UserEmailProjection> findEmailProjectionByPrefix(@Param("prefix") String prefix);

    Page<User> findByTenantIdAndStatus(Long tenantId, UserStatus status, Pageable pageable);
}

@Service
@Transactional(readOnly = true)
class UserQueryService {
    private final UserRepository users;

    UserQueryService(UserRepository users) {
        this.users = users;
    }

    Page<User> activeUsers(Long tenantId, int page, int size) {
        return users.findByTenantIdAndStatus(
            tenantId,
            UserStatus.ACTIVE,
            PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt"))
        );
    }

    Optional<User> activeUserWithOrders(Long id) {
        return users.findById(id);
    }
}
```

## Common Mistakes

```java
// WRONG: Fetching users and then iterating orders causes an N+1 query pattern.
@Service
class SlowUserService {
    private final UserRepository users;

    List<User> activeUsers() {
        return users.findByStatusOrderByCreatedAtDesc(UserStatus.ACTIVE);
    }
}

// CORRECT: Use join fetch or @EntityGraph when the query must load a relationship eagerly.
@Query("""
    select u
    from User u
    join fetch u.orders
    where u.status = :status
    """)
List<User> findActiveUsersWithOrders(@Param("status") UserStatus status);

// WRONG: Concatenating request input into JPQL enables malformed queries and data leaks.
@Query("select u from User u where u.email like :prefix || '%'")
List<User> findUsers(String prefix);

// CORRECT: Bind parameters with @Param and keep JPQL independent from raw input text.
@Query("select u from User u where u.email like concat(:prefix, '%')")
List<User> findUsersByPrefix(@Param("prefix") String prefix);

// WRONG: Unbounded list queries can load far more rows than an API client needs.
List<User> findAllByTenantId(Long tenantId);

// CORRECT: Use Pageable for controlled pages and predictable API behavior.
Page<User> findAllByTenantId(Long tenantId, Pageable pageable);

// WRONG: Native SQL projections without aliases are hard to bind reliably.
@Query(value = "select id, email from users where email like :prefix", nativeQuery = true)
List<UserEmailProjection> findUsers(String prefix);

// CORRECT: Name native SQL columns to match projection properties.
@Query(value = """
    select id, email, status
    from users
    where email like :prefix
    """, nativeQuery = true)
List<UserEmailProjection> findUsers(String prefix);
```

## Gotchas
- `join fetch` is useful for one query, but avoid fetching multiple bag collections in the same JPQL query because duplicate rows and Hibernate warnings can occur.
- `@EntityGraph` can replace `join fetch` when the query shape should stay simple, but it may not support every custom sort or projection.
- Projection interfaces reduce transferred data but do not return managed entities; use entities when lazy relationships must be updated later.
- Pagination still runs a count query for `Page`; use keyset pagination for very deep pages with large tables.
- `@Transactional(readOnly = true)` still opens a transaction and is still needed for lazy loading within repository/service calls.

## Related
- java/spring/boot-basics.md
- java/spring/spring-mvc.md
- java/spring/spring-boot-3-graalvm.md
