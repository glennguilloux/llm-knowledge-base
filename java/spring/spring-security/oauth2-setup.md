---
id: "java-spring-security-oauth2-setup"
title: "Spring Security OAuth2 Resource Server and Client"
language: "java"
category: "web"
subcategory: "security"
tags: ["spring", "spring-security", "oauth2", "jwt", "resource-server", "oidc"]
version: "17+"
retrieval_hint: "Spring Security OAuth2 resource server client JWT validation OIDC"
last_verified: "2026-05-22"
confidence: "high"
---

# Spring Security OAuth2 Resource Server and Client

## When to Use
- Securing APIs with OAuth2/OIDC tokens from external providers (Auth0, Keycloak, Okta)
- Microservice architectures where services validate JWT access tokens
- Single sign-on (SSO) with third-party identity providers
- Delegating authentication to an authorization server

## Standard Pattern

```java
// application.yml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.example.com/realms/myapp
          # Or use jwk-set-uri directly:
          # jwk-set-uri: https://auth.example.com/realms/myapp/protocol/openid-connect/certs

// Resource server configuration
@Configuration
@EnableWebSecurity
public class ResourceServerConfig {

    @Bean
    public SecurityFilterChain resourceServerFilterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())  // Stateless API — CSRF not needed
            .sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**").permitAll()
                .requestMatchers("/api/admin/**").hasAuthority("SCOPE_admin")
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(jwt -> jwt
                    .jwtAuthenticationConverter(jwtAuthenticationConverter())
                )
            )
            .build();
    }

    // Extract roles from JWT claims (e.g., realm_access.roles in Keycloak)
    @Bean
    public JwtAuthenticationConverter jwtAuthenticationConverter() {
        JwtGrantedAuthoritiesConverter grantedAuthoritiesConverter = new JwtGrantedAuthoritiesConverter();
        grantedAuthoritiesConverter.setAuthoritiesClaimName("roles");       // custom claim
        grantedAuthoritiesConverter.setAuthorityPrefix("ROLE_");

        JwtAuthenticationConverter authConverter = new JwtAuthenticationConverter();
        authConverter.setJwtGrantedAuthoritiesConverter(grantedAuthoritiesConverter);
        return authConverter;
    }
}

// OAuth2 client for login-with-Google/GitHub (web app, not API)
@Configuration
@EnableWebSecurity
public class OAuth2ClientConfig {

    @Bean
    public SecurityFilterChain clientFilterChain(HttpSecurity http) throws Exception {
        return http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/", "/login", "/error").permitAll()
                .anyRequest().authenticated()
            )
            .oauth2Login(oauth2 -> oauth2
                .defaultSuccessUrl("/dashboard", true)
                .userInfoEndpoint(userInfo -> userInfo
                    .userAuthoritiesMapper(userAuthoritiesMapper())
                )
            )
            .build();
    }

    // Map OAuth2 provider attributes to GrantedAuthority
    private GrantedAuthoritiesMapper userAuthoritiesMapper() {
        return (authorities) -> {
            Set<GrantedAuthority> mapped = new HashSet<>();
            authorities.forEach(authority -> {
                if (authority instanceof OAuth2UserAuthority oauth2Auth) {
                    String role = (String) oauth2Auth.getAttributes().get("role");
                    if (role != null) {
                        mapped.add(new SimpleGrantedAuthority("ROLE_" + role));
                    }
                }
                mapped.add(authority);
            });
            return mapped;
        };
    }
}

// Accessing the authenticated user in a controller
@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping("/me")
    public Map<String, Object> getCurrentUser(@AuthenticationPrincipal Jwt jwt) {
        return Map.of(
            "sub", jwt.getSubject(),
            "email", jwt.getClaimAsString("email"),
            "roles", jwt.getClaimAsStringList("roles")
        );
    }
}

// Resource server with custom token introspection (opaque tokens)
@Configuration
public class IntrospectionConfig {

    @Bean
    public SecurityFilterChain introspectionFilterChain(HttpSecurity http) throws Exception {
        return http
            .oauth2ResourceServer(oauth2 -> oauth2
                .opaqueToken(opaque -> opaque
                    .introspectionUri("https://auth.example.com/oauth2/introspect")
                    .introspectionClientCredentials("client-id", "client-secret")
                )
            )
            .build();
    }
}
```

## Common Mistakes

```java
// WRONG: Using jwtDecoder() bean with issuer-uri AND jwk-set-uri simultaneously
// Pick ONE — issuer-uri auto-configures jwk-set-uri via discovery
spring.security.oauth2.resourceserver.jwt.issuer-uri=https://...
spring.security.oauth2.resourceserver.jwt.jwk-set-uri=https://...

// CORRECT: Use only issuer-uri (Spring discovers jwk-set-uri automatically)
spring.security.oauth2.resourceserver.jwt.issuer-uri=https://auth.example.com/realms/myapp

// WRONG: Checking roles without mapping JWT claims to authorities
@PreAuthorize("hasRole('ADMIN')")  // Never matches — JWT has raw claim, not granted authority

// CORRECT: Configure JwtAuthenticationConverter to map claims
.oauth2ResourceServer(oauth2 -> oauth2
    .jwt(jwt -> jwt.jwtAuthenticationConverter(jwtAuthenticationConverter()))
);

// WRONG: Mixing stateless and session-based security in same filter chain
.csrf(csrf -> csrf.disable())  // Disables CSRF globally
.sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
// ...but oauth2Login() creates sessions internally

// CORRECT: Separate filter chains for API (stateless) and web login (session)
@Bean @Order(1)
public SecurityFilterChain apiChain(HttpSecurity http) { /* stateless JWT */ }
@Bean @Order(2)
public SecurityFilterChain webChain(HttpSecurity http) { /* session + OAuth2 login */ }
```

## Gotchas
- `spring-boot-starter-oauth2-resource-server` and `spring-boot-starter-oauth2-client` are separate dependencies — pick the right one
- OAuth2 resource server requires `spring-security-oauth2-jose` on the classpath for JWT decoding
- `SCOPE_read` is the default authority prefix for OAuth2 scopes — override with `setAuthorityPrefix("")`
- Keycloak puts roles in `realm_access.roles` (nested) — requires custom `JwtAuthenticationConverter`
- Token validation happens automatically with `issuer-uri` — Spring fetches the JWKS endpoint at startup
- If the authorization server is down at startup, the app fails to start — use `jwk-set-uri` as fallback
- `@AuthenticationPrincipal Jwt` works only with resource server; use `@AuthenticationPrincipal OAuth2User` for client login
- Opaque tokens require a network call to the introspection endpoint on every request — add caching or use JWTs

## Related
- java/spring/spring-security/jwt-auth.md
- java/spring/boot/actuator.md
- java/spring/mvc/cors-config.md
