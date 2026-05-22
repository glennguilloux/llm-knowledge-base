---
id: "java-spring-mvc-cors-config"
title: "Spring MVC CORS Configuration"
language: "java"
category: "web"
subcategory: "api-framework"
tags: ["spring", "mvc", "cors", "cross-origin", "security", "headers"]
version: "17+"
retrieval_hint: "Spring MVC CORS CrossOrigin configuration global WebMvcConfigurer"
last_verified: "2026-05-22"
confidence: "high"
---

# Spring MVC CORS Configuration

## When to Use
- Frontend on different origin calling the API (localhost:3000 → localhost:8080)
- Multi-domain deployments (api.example.com, app.example.com)
- Third-party integrations requiring cross-origin access
- Development environments with separate frontend/backend servers

## Standard Pattern

```java
// --- Global CORS configuration ---
@Configuration
public class CorsConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("https://app.example.com", "http://localhost:3000")
            .allowedMethods("GET", "POST", "PUT", "DELETE", "PATCH")
            .allowedHeaders("*")
            .allowCredentials(true)
            .maxAge(3600);  // Cache preflight for 1 hour
    }
}

// --- Per-controller CORS ---
@RestController
@RequestMapping("/api/users")
@CrossOrigin(origins = "https://app.example.com")
public class UserController {
    // All methods inherit the CORS config
}

// --- Per-method CORS ---
@RestController
public class ApiController {
    @GetMapping("/public/data")
    @CrossOrigin(origins = "*")  // Public endpoint
    public Data getPublicData() {
        return dataService.getPublic();
    }

    @GetMapping("/private/data")
    @CrossOrigin(origins = "https://app.example.com", allowCredentials = "true")
    public Data getPrivateData() {
        return dataService.getPrivate();
    }
}

// --- CORS with Spring Security ---
@Configuration
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.cors(cors -> cors.configurationSource(corsConfigurationSource()))
            .csrf(csrf -> csrf.disable())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**").permitAll()
                .anyRequest().authenticated()
            );
        return http.build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(List.of("https://app.example.com"));
        config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
        config.setAllowedHeaders(List.of("*"));
        config.setAllowCredentials(true);
        config.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/api/**", config);
        return source;
    }
}
```

## Common Mistakes

```java
// WRONG: Using allowedOrigins("*") with allowCredentials(true)
config.setAllowedOrigins(List.of("*"));
config.setAllowCredentials(true);  // Browsers reject this!

// CORRECT: Use specific origins with credentials
config.setAllowedOrigins(List.of("https://app.example.com"));
config.setAllowCredentials(true);

// WRONG: CORS not working with Spring Security (security filters run first)
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**").allowedOrigins("*");
    }
}
// Security filter blocks preflight OPTIONS requests!

// CORRECT: Configure CORS in Security config
http.cors(cors -> cors.configurationSource(corsConfigurationSource()))

// WRONG: Not allowing OPTIONS method
config.setAllowedMethods(List.of("GET", "POST"));  // Preflight OPTIONS fails!

// CORRECT: OPTIONS is handled automatically by Spring, but ensure methods are listed
config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
```

## Gotchas
- When using Spring Security, CORS must be configured in SecurityFilterChain, not WebMvcConfigurer
- Preflight `OPTIONS` requests are handled automatically — don't create explicit OPTIONS endpoints
- `@CrossOrigin` on a method overrides class-level `@CrossOrigin`
- `allowedOriginPatterns("*")` works with credentials (unlike `allowedOrigins("*")`)
- `maxAge` controls how long preflight responses are cached by browsers
- CORS headers are added by Spring's `CorsFilter` — must run before authentication filters
- `allowCredentials = true` means cookies/auth headers are sent — use specific origins
- Multiple CORS configurations can coexist — most specific match wins

## Related
- java/spring/spring-mvc.md
- java/spring/spring-security/jwt-auth.md
- java/spring/boot-basics.md
