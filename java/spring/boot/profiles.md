---
id: "java-spring-boot-profiles"
title: "Spring Boot Profiles"
language: "java"
category: "web"
subcategory: "api-framework"
tags: ["spring", "boot", "profiles", "environment", "configuration", "dev", "prod"]
version: "17+"
retrieval_hint: "Spring Boot profiles dev staging prod environment configuration"
last_verified: "2026-05-22"
confidence: "high"
---

# Spring Boot Profiles

## When to Use
- Different database/cache settings per environment (dev, staging, prod)
- Enabling/disabling features per environment (debug endpoints, Swagger)
- Testing with different configurations (in-memory DB for tests)
- Conditional bean registration based on environment

## Standard Pattern

```java
// --- application.yml (base config) ---
// spring:
//   datasource:
//     url: jdbc:postgresql://localhost:5432/mydb
//   jpa:
//     hibernate:
//       ddl-auto: validate

// --- application-dev.yml ---
// spring:
//   datasource:
//     url: jdbc:h2:mem:devdb
//   jpa:
//     hibernate:
//       ddl-auto: create-drop
//   h2:
//     console:
//       enabled: true
// logging:
//   level:
//     com.example: DEBUG

// --- application-prod.yml ---
// spring:
//   datasource:
//     url: ${DATABASE_URL}
//     hikari:
//       maximum-pool-size: 20
//   jpa:
//     hibernate:
//       ddl-auto: validate
// logging:
//   level:
//     root: WARN

// --- Profile-specific beans ---
@Configuration
@Profile("dev")
public class DevConfig {
    @Bean
    public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .build();
    }
}

@Configuration
@Profile("prod")
public class ProdConfig {
    @Bean
    public DataSource dataSource(
            @Value("${spring.datasource.url}") String url,
            @Value("${spring.datasource.username}") String user,
            @Value("${spring.datasource.password}") String pass) {
        HikariDataSource ds = new HikariDataSource();
        ds.setJdbcUrl(url);
        ds.setUsername(user);
        ds.setPassword(pass);
        return ds;
    }
}

// --- Conditional on profile ---
@Service
@Profile("!prod")  // Active in all profiles except prod
public class DevDataService {
    public void loadTestData() {
        // Only in dev/test
    }
}

// --- Activate profiles ---
// java -jar app.jar --spring.profiles.active=prod
// SPRING_PROFILES_ACTIVE=prod java -jar app.jar
// In tests: @ActiveProfiles("test")
```

## Common Mistakes

```java
// WRONG: Hardcoding environment-specific values
@Bean
public DataSource dataSource() {
    return new HikariDataSource("jdbc:postgresql://prod-server:5432/db");
}

// CORRECT: Use profile-specific config files
// application-prod.yml: spring.datasource.url=${DATABASE_URL}

// WRONG: Using @Profile on @Component without considering default behavior
@Service
@Profile("dev")
public class NotificationService { }  // Missing in prod!

// CORRECT: Use default profile or provide prod implementation
@Service
public interface NotificationService { }

@Service
@Profile("dev")
public class EmailNotificationService implements NotificationService { }

@Service
@Profile("prod")
public class SqsNotificationService implements NotificationService { }

// WRONG: Not setting default profile
// No default → uses application.yml only, may fail with missing prod config

// CORRECT: Set default in application.yml
// spring.profiles.default: dev
```

## Gotchas
- `application.yml` is always loaded; profile-specific files override it
- `@Profile("!prod")` means "active in all profiles except prod"
- Multiple profiles can be active: `--spring.profiles.active=prod,us-east`
- `@Profile` works on `@Component`, `@Service`, `@Configuration`, `@Bean`
- Use `@ActiveProfiles("test")` in tests to activate test profiles
- Profile-specific properties win over base properties (later profiles override earlier)
- `spring.profiles.active` can be set via env var, system prop, or command line
- `@ConditionalOnProperty` is an alternative to `@Profile` for feature flags

## Related
- java/spring/boot-basics.md
- java/spring/boot/configuration-properties.md
- java/testing/spring-boot-testing.md
