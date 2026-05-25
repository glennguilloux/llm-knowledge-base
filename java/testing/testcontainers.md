---
id: "java-testing-testcontainers"
title: "Testcontainers: Integration Testing with Docker"
language: "java"
category: "testing"
subcategory: "integration-testing"
tags: ["testcontainers", "docker", "integration", "postgresql", "redis", "kafka"]
version: "17+"
retrieval_hint: "Testcontainers Docker PostgreSQL Redis Kafka integration test container"
last_verified: "2026-05-24"
confidence: "high"
---

# Testcontainers: Integration Testing with Docker

## When to Use
- Integration tests requiring real databases (PostgreSQL, MySQL, MongoDB)
- Testing with real Redis, Kafka, or other infrastructure services
- Replacing H2 with real PostgreSQL for accurate query testing
- Ensuring tests run consistently across environments (no "works on my machine")

## Standard Pattern

```java
// pom.xml dependency
// <dependency>
//   <groupId>org.testcontainers</groupId>
//   <artifactId>postgresql</artifactId>
//   <scope>test</scope>
// </dependency>

import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@Testcontainers
class UserRepositoryIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test")
        .withInitScript("schema.sql");  // Run on startup

    @Container
    static GenericContainer<?> redis = new GenericContainer<>("redis:7-alpine")
        .withExposedPorts(6379);

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.redis.host", redis::getHost);
        registry.add("spring.redis.port", () -> redis.getMappedPort(6379));
    }

    @Autowired
    private UserRepository userRepository;

    @Test
    void shouldSaveAndRetrieveUser() {
        User user = new User(null, "Alice", "alice@test.com");
        User saved = userRepository.save(user);

        assertThat(saved.getId()).isNotNull();
        assertThat(userRepository.findById(saved.getId()))
            .isPresent()
            .get()
            .extracting(User::getName)
            .isEqualTo("Alice");
    }

    @Test
    void shouldFindByEmail() {
        userRepository.save(new User(null, "Bob", "bob@test.com"));

        assertThat(userRepository.findByEmail("bob@test.com"))
            .isPresent()
            .get()
            .extracting(User::getName)
            .isEqualTo("Bob");
    }
}

// --- Reusable container (shared across test classes) ---
public abstract class AbstractIntegrationTest {
    static final PostgreSQLContainer<?> postgres;

    static {
        postgres = new PostgreSQLContainer<>("postgres:16-alpine");
        postgres.start();
    }

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }
}
```

## Common Mistakes

```java
// WRONG: Starting container in every test method
@Test
void test1() {
    PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16");
    postgres.start();  // Slow — starts new container per test
}

// CORRECT: Use @Container with static field (starts once per test class)
@Container
static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

// WRONG: Not using @DynamicPropertySource (Spring uses default datasource)
@Testcontainers
class MyTest {
    @Container
    static PostgreSQLContainer<?> postgres = ...;
    // Spring still connects to default datasource!
}

// CORRECT: Wire container properties to Spring
@DynamicPropertySource
static void configureProperties(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.url", postgres::getJdbcUrl);
}

// WRONG: Using latest tag (non-deterministic)
new PostgreSQLContainer<>("postgres:latest")  // Different versions across runs

// CORRECT: Pin to specific version
new PostgreSQLContainer<>("postgres:16-alpine")

// WRONG: Not cleaning up data between tests
@Test
void test1() {
    userRepository.save(new User(...));  // Data persists to test2!
}

// CORRECT: Use @Transactional on test class (auto-rollback)
@Transactional
class UserRepositoryIntegrationTest { ... }
```

## Gotchas
- `@Container` + `static` = one container per test class; non-static = one per test method
- `@DynamicPropertySource` wires container connection details to Spring's config
- Testcontainers requires Docker — won't work in environments without Docker
- Use `withInitScript("schema.sql")` for database setup (runs once on container start)
- `@Transactional` on test methods rolls back after each test — clean state
- Container startup takes 5-10 seconds — use static containers for speed
- `GenericContainer` works for any Docker image; specialized classes exist for PostgreSQL, Kafka, etc.
- Containers are automatically stopped when the JVM exits (via shutdown hook)

## Related
- java/testing/mockito-deep.md
- java/testing/spring-boot-testing.md
- java/spring/spring-data/jpa-repositories.md
