---
id: "java-spring-configuration-properties"
title: "Spring Boot Configuration Properties"
language: "java"
category: "web"
subcategory: "configuration"
tags: ["spring-boot", "configuration-properties", "EnableConfigurationProperties", "validation", "binding", "records", "relaxed-binding"]
version: "17+"
retrieval_hint: "Spring configuration properties EnableConfigurationProperties validation binding immutable records relaxed binding"
last_verified: "2026-06-20"
confidence: "medium"
---

# Spring Boot Configuration Properties

## When to Use
- Grouping related configuration values into typed, testable objects.
- Validating required settings during application startup.
- Binding lists, durations, durations units, and nested records from `application.yml` or environment variables.
- Avoiding scattered `@Value` annotations across services.

## Standard Pattern

```java
package com.example.catalog.config;

import jakarta.validation.constraints.*;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.validation.annotation.Validated;

import java.time.Duration;

@Configuration(proxyBeanMethods = false)
@EnableConfigurationProperties(BillingProperties.class)
class BillingConfiguration {

    @Bean
    EmailClient emailClient(BillingProperties properties) {
        return new EmailClient(properties.email().fromAddress(), properties.email().adminRecipients());
    }
}

@Validated
@ConfigurationProperties(prefix = "billing")
public record BillingProperties(Email email) {

    @Valid
    public record Email(
        @NotBlank String fromAddress,
        @NotEmpty List<String> adminRecipients,
        @NotNull Duration retryAfter
    ) {}
}

class EmailClient {
    EmailClient(String fromAddress, List<String> adminRecipients) {
    }
}
```

```yaml
billing:
  email:
    from-address: noreply@example.invalid
    admin-recipients:
      - ops@example.invalid
    retry-after: 30s
```

## Common Mistakes

```java
// WRONG: Scattering unrelated @Value annotations across multiple services.
@Service
class EmailService {
    @Value("${billing.email.from-address}")
    private String fromAddress;
}

// CORRECT: Bind a typed configuration object once and inject it where needed.
@Service
class EmailService {
    private final BillingProperties properties;

    EmailService(BillingProperties properties) {
        this.properties = properties;
    }
}

// WRONG: Using mutable configuration without validation allows invalid startup state.
@ConfigurationProperties(prefix = "billing.email")
class EmailProperties {
    private String fromAddress;
}

// CORRECT: Use records, classes, or nested records with Bean Validation constraints.
@Validated
@ConfigurationProperties(prefix = "billing.email")
record EmailProperties(@NotBlank String fromAddress) {}

// WRONG: Forgetting to enable configuration properties scanning or registration.
record EmailProperties(@NotBlank String fromAddress) {}

// CORRECT: Use @EnableConfigurationProperties or @ConfigurationPropertiesScan.
@Configuration
@EnableConfigurationProperties(EmailProperties.class)
class EmailConfiguration {}

// WRONG: Binding duration text without a unit can depend on converter defaults.
record RetryProperties(Duration retryAfter) {}

// CORRECT: Use explicit units in configuration such as 30s, 5m, or 1h.
record RetryProperties(Duration retryAfter) {}
```

## Gotchas
- Relaxed binding maps `from-address` in YAML or environment variables to `fromAddress` in Java properties.
- Records support constructor binding by default; mutable classes need a no-args constructor and setters.
- `@ConfigurationProperties` classes are not automatically component-scanned unless scanning or explicit enablement is configured.
- Bean Validation constraints require `@Validated` on the properties type and the validation starter on the classpath.
- Do not store secrets directly in plain configuration files; prefer environment variables or a secrets manager.

## Related
- java/spring/boot-basics.md
- java/spring/spring-mvc.md
- java/spring/spring-boot-3-graalvm.md
