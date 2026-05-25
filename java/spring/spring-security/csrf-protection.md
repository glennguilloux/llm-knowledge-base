---
id: "java-spring-security-csrf-protection"
title: "Spring Security CSRF Protection"
language: "java"
category: "web"
subcategory: "security"
tags: ["spring", "spring-security", "csrf", "xsrf", "spa", "cookie"]
version: "17+"
retrieval_hint: "Spring Security CSRF token protection SPA cookie XSRF stateless"
last_verified: "2026-05-24"
confidence: "high"
---

# Spring Security CSRF Protection

## When to Use
- Server-rendered forms (Thymeleaf, JSP) that submit via POST — CSRF is mandatory
- Single-page applications (React, Angular, Vue) with session-based authentication
- APIs consumed by browsers with cookies — CSRF tokens prevent cross-site request forgery
- Environments where the frontend and backend share the same origin

## Standard Pattern

```java
// Default behavior — CSRF is enabled by default in Spring Security
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            // CSRF is ON by default — no explicit config needed for server-rendered forms
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/login", "/register").permitAll()
                .anyRequest().authenticated()
            )
            .formLogin(form -> form
                .loginPage("/login")
                .defaultSuccessUrl("/dashboard")
            )
            .build();
    }
}

// SPA with CookieCsrfTokenRepository (Angular/React/Vue compatible)
@Configuration
@EnableWebSecurity
public class SpaSecurityConfig {

    @Bean
    public SecurityFilterChain spaFilterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf
                .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
                // withHttpOnlyFalse — JS must read the cookie to send X-XSRF-TOKEN header
                .csrfTokenRequestHandler(new SpaCsrfTokenRequestHandler())
            )
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**").permitAll()
                .anyRequest().authenticated()
            )
            .build();
    }
}

// Custom handler that reads token from header OR request parameter
// (for SPAs that send X-XSRF-TOKEN header from a cookie)
@Component
public class SpaCsrfTokenRequestHandler implements CsrfTokenRequestAttributeHandler {

    private final CsrfTokenRequestAttributeHandler delegate = new XorCsrfTokenRequestAttributeHandler();

    @Override
    public void handle(HttpServletRequest request, HttpServletResponse response,
                       Supplier<CsrfToken> csrfToken) {
        delegate.handle(request, response, csrfToken);
    }

    @Override
    public String resolveCsrfTokenValue(HttpServletRequest request, CsrfToken csrfToken) {
        // Check header first (SPA sends X-XSRF-TOKEN), then fall back to parameter
        String headerValue = request.getHeader(csrfToken.getHeaderName());
        if (headerValue != null) {
            return headerValue;
        }
        return delegate.resolveCsrfTokenValue(request, csrfToken);
    }
}

// Stateful CSRF using HttpSession (legacy approach)
@Bean
public CsrfTokenRepository csrfTokenRepository() {
    HttpSessionCsrfTokenRepository repository = new HttpSessionCsrfTokenRepository();
    repository.setHeaderName("X-CSRF-TOKEN");
    repository.setParameterName("_csrf");
    return repository;
}

// Disabling CSRF for stateless REST APIs (JWT/bearer token — no cookies)
@Configuration
@EnableWebSecurity
public class RestApiConfig {

    @Bean
    public SecurityFilterChain restFilterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())  // Safe: no cookies = no CSRF risk
            .sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .build();
    }
}
```

## Common Mistakes

```java
// WRONG: Disabling CSRF on APIs that use cookies for authentication
.csrf(csrf -> csrf.disable())  // Cookies + no CSRF = vulnerable to CSRF attacks

// CORRECT: Keep CSRF enabled for cookie-based auth, use CookieCsrfTokenRepository
.csrf(csrf -> csrf
    .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
)

// WRONG: Using CSRF disable for ALL APIs including those behind form login
// Form login uses sessions (cookies) — CSRF protection is critical
.csrf(csrf -> csrf.disable())  // Opens form-login endpoints to CSRF

// CORRECT: Disable CSRF only for stateless APIs
// For mixed apps, use multiple filter chains:
@Bean @Order(1)
public SecurityFilterChain apiChain(HttpSecurity http) throws Exception {
    return http
        .securityMatcher("/api/**")
        .csrf(csrf -> csrf.disable())  // API uses JWT — no cookies
        .build();
}

@Bean @Order(2)
public SecurityFilterChain webChain(HttpSecurity http) throws Exception {
    return http
        .csrf(csrf -> csrf
            .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
        )  // Web uses sessions — CSRF required
        .build();
}

// WRONG: Not including CSRF token in AJAX POST requests
// The browser blocks the request with 403 Forbidden

// CORRECT: Include X-XSRF-TOKEN header in fetch/axios
// Axios auto-reads XSRF-TOKEN cookie:
axios.defaults.xsrfHeaderName = 'X-XSRF-TOKEN';
axios.defaults.xsrfCookieName = 'XSRF-TOKEN';
```

## Gotchas
- CSRF is **enabled by default** in Spring Security — you only configure it, not enable it
- `SessionCreationPolicy.STATELESS` does NOT disable CSRF — you must explicitly call `csrf.disable()`
- `CookieCsrfTokenRepository.withHttpOnlyFalse()` is required for JavaScript to read the XSRF cookie
- Spring Security 6+ uses `XorCsrfTokenRequestAttributeHandler` by default — mitigates BREACH attacks
- The CSRF token is a `Supplier<CsrfToken>` — it's lazily generated on first access
- GET/HEAD/TRACE/OPTIONS requests never require CSRF tokens (they should be idempotent)
- Testing CSRF: use `MockMvc` with `.with(csrf())` from `SecurityMockMvcRequestPostProcessors`
- If using `SameSite=Lax` cookies (default since Spring Security 5.7), CSRF risk is reduced but not eliminated
- The CSRF cookie name defaults to `XSRF-TOKEN`; the header name defaults to `X-XSRF-TOKEN`

## Related
- java/spring/spring-security/jwt-auth.md
- java/spring/mvc/cors-config.md
- java/spring/spring-security/oauth2-setup.md
