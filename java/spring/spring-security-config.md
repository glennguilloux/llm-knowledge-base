---
id: "java-spring-security-config"
title: "Spring Security Filter Chain Configuration"
language: "java"
category: "web"
subcategory: "security"
tags: ["spring", "security", "SecurityFilterChain", "HttpSecurity", "authorization", "csrf", "stateless", "password-encoder"]
version: "17+"
retrieval_hint: "Spring Security SecurityFilterChain HttpSecurity authorize requests password encoding CSRF stateless authorization"
last_verified: "2026-06-20"
confidence: "medium"
---

# Spring Security Filter Chain Configuration

## When to Use
- Configuring request authorization for Spring MVC, WebFlux, or REST API applications.
- Choosing when CSRF protection should stay enabled or can be disabled for stateless bearer-token APIs.
- Encoding passwords and wiring authentication details safely.
- Separating public endpoints, user endpoints, and administrative endpoints.

## Standard Pattern

```java
package com.example.catalog.security;

import org.springframework.context.annotation.*;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
class SecurityConfig {

    @Bean
    SecurityFilterChain apiSecurity(HttpSecurity http) throws Exception {
        http
            // Keep CSRF enabled for browser cookie sessions. Disable only for stateless APIs.
            .csrf(csrf -> csrf.disable())
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health", "/actuator/health/readiness").permitAll()
                .requestMatchers(HttpMethod.POST, "/api/orders/**").hasAuthority("ORDER_WRITE")
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .httpBasic(basic -> basic.disable());

        return http.build();
    }

    @Bean
    PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
```

## Common Mistakes

```java
// WRONG: Disabling CSRF in a cookie-based browser application leaves state-changing requests exposed.
@Bean
SecurityFilterChain browserSecurity(HttpSecurity http) throws Exception {
    return http.csrf(csrf -> csrf.disable()).build();
}

// CORRECT: Keep CSRF protection for browser sessions and disable it only for stateless token APIs.
@Bean
SecurityFilterChain browserSecurity(HttpSecurity http) throws Exception {
    return http.build();
}

// WRONG: Using raw or reversible passwords for stored credentials.
@Bean
PasswordEncoder passwordEncoder() {
    return NoOpPasswordEncoder.getInstance();
}

// CORRECT: Use an adaptive one-way password encoder such as BCrypt.
@Bean
PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
}

// WRONG: Authorizing broad controller paths before narrow administrative paths.
.authorizeHttpRequests(auth -> auth
    .requestMatchers("/api/**").authenticated()
    .requestMatchers("/api/admin/**").hasRole("ADMIN"))

// CORRECT: Place specific matchers before broad matchers so admin rules are not shadowed.
.authorizeHttpRequests(auth -> auth
    .requestMatchers("/api/admin/**").hasRole("ADMIN")
    .requestMatchers("/api/**").authenticated()
    .anyRequest().denyAll())

// WRONG: Treating roles and authorities as interchangeable.
.requestMatchers("/api/admin/**").hasAuthority("ADMIN")

// CORRECT: Use hasRole for role-prefixed authorities and hasAuthority for exact authority names.
.requestMatchers("/api/admin/**").hasRole("ADMIN")
```

## Gotchas
- `hasRole("ADMIN")` checks for an authority named `ROLE_ADMIN`; `hasAuthority("ADMIN")` checks for `ADMIN`.
- Request matcher order matters; narrow administrative or health-check rules should appear before broad application rules.
- CSRF protection should remain enabled for browser cookie sessions and be disabled only when the API is stateless and uses bearer tokens.
- A single application can define multiple `SecurityFilterChain` beans with different `securityMatcher` values for APIs, admin UIs, and actuator endpoints.
- Method-level security needs `@EnableMethodSecurity` in addition to HTTP-level `SecurityFilterChain` configuration.

## Related
- java/spring/boot-basics.md
- java/spring/spring-mvc.md
- java/spring/spring-boot-3-graalvm.md
