---
id: "java-spring-boot-configuration-properties"
title: "Spring Boot Configuration Properties"
language: "java"
category: "web"
subcategory: "api-framework"
tags: ["spring", "boot", "configuration", "properties", "yaml", "type-safe"]
version: "17+"
retrieval_hint: "Spring Boot ConfigurationProperties type-safe configuration YAML properties"
last_verified: "2026-05-24"
confidence: "high"
---

# Spring Boot Configuration Properties

## When to Use
- Binding application.yml/properties to strongly-typed Java objects
- Grouping related configuration values (database, cache, feature flags)
- Validating configuration at startup with Bean Validation
- Replacing scattered `@Value` annotations with organized config classes

## Standard Pattern

```java
// --- application.yml ---
// app:
//   database:
//     url: jdbc:postgresql://localhost:5432/mydb
//     pool-size: 20
//     timeout: 30s
//   cache:
//     ttl: 300
//     max-entries: 1000
//   features:
//     new-dashboard: true
//     beta-api: false

package com.example.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;
import org.springframework.validation.annotation.Validated;
import jakarta.validation.constraints.*;
import java.time.Duration;
import java.util.List;
import java.util.Map;

@ConfigurationProperties(prefix = "app")
@Validated
public record AppConfig(
    @NotNull DatabaseConfig database,
    CacheConfig cache,
    Map<String, Boolean> features
) {
    public record DatabaseConfig(
        @NotBlank String url,
        @Min(1) @Max(100) @DefaultValue("10") int poolSize,
        @NotNull Duration timeout
    ) {}

    public record CacheConfig(
        @DefaultValue("300") int ttl,
        @DefaultValue("1000") int maxEntries
    ) {}
}

// --- Enable in main class ---
@SpringBootApplication
@EnableConfigurationProperties(AppConfig.class)
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}

// --- Inject and use ---
@Service
public class UserService {
    private final AppConfig config;

    public UserService(AppConfig config) {
        this.config = config;
    }

    public void doWork() {
        String dbUrl = config.database().url();
        int poolSize = config.database().poolSize();
        boolean betaEnabled = config.features().getOrDefault("beta-api", false);
    }
}
```

## Common Mistakes

```java
// WRONG: Using @Value everywhere
@Value("${app.database.url}")
private String dbUrl;

@Value("${app.database.pool-size}")
private int poolSize;  // Scattered, no validation, no grouping

// CORRECT: Use @ConfigurationProperties for grouped config
@ConfigurationProperties(prefix = "app.database")
public record DatabaseConfig(String url, int poolSize) {}

// WRONG: Not validating config (fails at runtime, not startup)
@ConfigurationProperties(prefix = "app")
public class AppConfig {
    private String databaseUrl;  // Could be null at runtime
}

// CORRECT: Add @Validated and constraints
@ConfigurationProperties(prefix = "app")
@Validated
public record AppConfig(@NotNull DatabaseConfig database) {}

// WRONG: Using mutable fields
@ConfigurationProperties(prefix = "app")
public class AppConfig {
    private String url;  // Mutable, no immutability guarantee
    public void setUrl(String url) { this.url = url; }
}

// CORRECT: Use records (immutable)
@ConfigurationProperties(prefix = "app")
public record AppConfig(String url) {}
```

## Gotchas
- `@ConfigurationProperties` requires `@EnableConfigurationProperties` or `@ConfigurationPropertiesScan`
- Records work with Spring Boot 3+ — use `@DefaultValue` for optional fields
- `Duration` type auto-parses strings like "30s", "5m", "1h" from YAML
- Validation annotations (`@NotNull`, `@Min`) require `@Validated` on the class
- Property names use relaxed binding: `pool-size`, `poolSize`, `POOL_SIZE` all work
- Use `@DefaultValue` on record parameters for optional fields with defaults
- `@ConfigurationProperties` classes are validated at startup — fails fast on bad config
- Prefix must be lowercase kebab-case: `app.database` not `App.Database`

## Related
- java/spring/boot-basics.md
- java/spring/boot/profiles.md
- java/spring/spring-data/jpa-repositories.md
