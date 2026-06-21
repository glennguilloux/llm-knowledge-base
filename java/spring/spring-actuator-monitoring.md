---
id: "java-spring-actuator-monitoring"
title: "Spring Boot Actuator Monitoring Endpoints"
language: "java"
category: "web"
subcategory: "observability"
tags: ["spring-boot", "actuator", "health", "readiness", "metrics", "prometheus", "monitoring", "info"]
version: "17+"
retrieval_hint: "Spring Boot Actuator health readiness metrics endpoints Prometheus info exposure monitoring"
last_verified: "2026-06-20"
confidence: "medium"
---

# Spring Boot Actuator Monitoring Endpoints

## When to Use
- Exposing health, readiness, liveness, info, and metrics endpoints for platforms and operators.
- Publishing Prometheus metrics from a Spring Boot service.
- Controlling which actuator endpoints are exposed over HTTP.
- Keeping operational visibility separate from business API endpoints.

## Standard Pattern

```java
package com.example.catalog.monitoring;

import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.config.MeterRegistryCustomizer;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
class MonitoringConfiguration {

    /*
    management:
      endpoints:
        web:
          exposure:
            include: health,info,metrics,prometheus
      endpoint:
        health:
          probes:
            enabled: true
          show-details: when_authorized
          roles: ops
      metrics:
        tags:
          application: ${spring.application.name}
    */

    @Bean
    MeterRegistryCustomizer<MeterRegistry> metricsCommonTags() {
        return registry -> registry.config()
            .commonTags("service", "catalog", "runtime", "jvm");
    }

    @Bean
    HealthIndicator catalogReadinessHealthIndicator() {
        return () -> Health.up()
            .withDetail("database", "ready")
            .withDetail("message-broker", "ready")
            .build();
    }
}
```

## Common Mistakes

```java
// WRONG: Exposing every actuator endpoint can leak configuration and runtime internals.
// management.endpoints.web.exposure.include: "*"

// CORRECT: Expose only the endpoints needed by the platform and operators.
// management.endpoints.web.exposure.include: health,info,metrics,prometheus

// WRONG: Always showing health details can disclose dependency names and internal state.
management:
  endpoint:
    health:
      show-details: always

// CORRECT: Show details only to authorized roles.
management:
  endpoint:
    health:
      show-details: when_authorized
      roles: ops

// WRONG: Treating liveness and readiness as the same signal.
management:
  endpoint:
    health:
      probes:
        enabled: false

// CORRECT: Enable probes so Kubernetes can distinguish restart-worthy failures from temporary unavailability.
management:
  endpoint:
    health:
      probes:
        enabled: true

// WRONG: Publishing metrics without common tags makes dashboards harder to filter.
management:
  metrics:
    tags: {}

// CORRECT: Add stable common tags such as service, team, and environment.
management:
  metrics:
    tags:
      service: catalog
      team: platform
```

## Gotchas
- `/actuator/health` is a summary endpoint; `/actuator/health/readiness` and `/actuator/health/liveness` are separate probe signals when probes are enabled.
- The Prometheus endpoint requires the Micrometer Prometheus registry dependency in addition to actuator exposure.
- `management.endpoints.web.exposure.include` is an allow-list; unlisted endpoints are not exposed over HTTP.
- Endpoints such as `env`, `beans`, and `threaddump` can reveal sensitive implementation details and should not be broadly exposed.
- Health details controlled by `show-details` still require authorization roles when `when_authorized` is selected.

## Related
- java/spring/boot-basics.md
- java/spring/spring-mvc.md
- java/spring/spring-boot-3-graalvm.md
