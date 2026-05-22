---
id: "java-spring-boot-actuator"
title: "Spring Boot Actuator Endpoints"
language: "java"
category: "web"
subcategory: "monitoring"
tags: ["spring", "boot", "actuator", "health", "metrics", "monitoring"]
version: "17+"
retrieval_hint: "Spring Boot Actuator health metrics monitoring endpoints info custom"
last_verified: "2026-05-22"
confidence: "high"
---

# Spring Boot Actuator Endpoints

## When to Use
- Health checks for load balancers and Kubernetes probes
- Application metrics (JVM memory, HTTP request latency, custom counters)
- Production monitoring and alerting integration
- Exposing application info (version, build time, git commit)

## Standard Pattern

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
```

```java
// --- application.yml ---
// management:
//   endpoints:
//     web:
//       exposure:
//         include: health,info,metrics,prometheus
//   endpoint:
//     health:
//       show-details: when_authorized
//   health:
//     db:
//       enabled: true
//     diskspace:
//       enabled: true

// --- Custom health indicator ---
@Component
public class ExternalServiceHealthIndicator implements HealthIndicator {
    private final ExternalServiceClient client;

    public ExternalServiceHealthIndicator(ExternalServiceClient client) {
        this.client = client;
    }

    @Override
    public Health health() {
        try {
            boolean isUp = client.ping();
            if (isUp) {
                return Health.up()
                    .withDetail("service", "external-api")
                    .withDetail("latency_ms", client.getLastLatency())
                    .build();
            }
            return Health.down()
                .withDetail("service", "external-api")
                .withDetail("reason", "ping failed")
                .build();
        } catch (Exception e) {
            return Health.down()
                .withException(e)
                .build();
        }
    }
}

// --- Custom metrics ---
@Service
public class OrderService {
    private final Counter orderCounter;
    private final Timer orderTimer;

    public OrderService(MeterRegistry registry) {
        this.orderCounter = Counter.builder("orders.created")
            .description("Total orders created")
            .tag("source", "api")
            .register(registry);
        this.orderTimer = Timer.builder("orders.processing.time")
            .description("Order processing time")
            .register(registry);
    }

    public Order createOrder(OrderRequest request) {
        return orderTimer.record(() -> {
            Order order = doCreateOrder(request);
            orderCounter.increment();
            return order;
        });
    }
}

// --- Expose build info ---
// In pom.xml, add spring-boot-maven-plugin with build-info goal:
// <plugin>
//   <groupId>org.springframework.boot</groupId>
//   <artifactId>spring-boot-maven-plugin</artifactId>
//   <executions>
//     <execution>
//       <goals><goal>build-info</goal></goals>
//     </execution>
//   </executions>
// </plugin>
```

## Common Mistakes

```java
// WRONG: Exposing all actuator endpoints in production
// management.endpoints.web.exposure.include=*
// Exposes /env, /beans, /configprops — security risk!

// CORRECT: Only expose necessary endpoints
// management.endpoints.web.exposure.include=health,info,metrics

// WRONG: Showing health details to everyone
// management.endpoint.health.show-details=always
// Leaks database connection info, disk paths, etc.

// CORRECT: Restrict details to authorized users
// management.endpoint.health.show-details=when_authorized

// WRONG: Not securing actuator endpoints
// Anyone can access /actuator/env and see secrets

// CORRECT: Add security rules
@Configuration
public class ActuatorSecurityConfig {
    @Bean
    public SecurityFilterChain actuatorSecurity(HttpSecurity http) throws Exception {
        http.securityMatchers(matchers -> matchers.requestMatchers("/actuator/**"))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health").permitAll()
                .requestMatchers("/actuator/**").hasRole("ADMIN")
            );
        return http.build();
    }
}
```

## Gotchas
- Actuator endpoints are at `/actuator/*` by default (configurable via `management.endpoints.web.base-path`)
- `/actuator/health` returns `UP`/`DOWN` — Kubernetes uses this for liveness/readiness probes
- Custom health indicators auto-register if they implement `HealthIndicator`
- `MeterRegistry` is auto-configured — inject it to create custom metrics
- Prometheus endpoint requires `micrometer-registry-prometheus` dependency
- `/actuator/info` shows nothing by default — use `build-info` goal or custom `InfoContributor`
- Health details are hidden by default — set `show-details=when_authorized` for debugging
- Actuator endpoints can be on a separate port: `management.server.port=8081`

## Related
- java/spring/boot-basics.md
- java/spring/boot/profiles.md
- patterns/health-checks.md
