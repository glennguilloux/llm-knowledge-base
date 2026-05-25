---
id: "java-spring-security-jwt-auth"
title: "Spring Security JWT Authentication"
language: "java"
category: "web"
subcategory: "authentication"
tags: ["spring", "security", "jwt", "authentication", "filter", "bearer"]
version: "17+"
retrieval_hint: "Spring Security JWT authentication filter bearer token"
last_verified: "2026-05-24"
confidence: "high"
---

# Spring Security JWT Authentication

## When to Use
- Stateless API authentication
- Token-based auth for microservices
- Securing REST endpoints

## Standard Pattern

```java
import java.time.Duration;
import java.time.Instant;
import java.util.Date;

// Security configuration
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    private final JwtAuthenticationFilter jwtFilter;

    public SecurityConfig(JwtAuthenticationFilter jwtFilter) {
        this.jwtFilter = jwtFilter;
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class)
            .build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}

// JWT filter
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtService jwtService;
    private final UserDetailsService userDetailsService;

    @Override
    protected void doFilterInternal(
        HttpServletRequest request,
        HttpServletResponse response,
        FilterChain filterChain
    ) throws ServletException, IOException {
        String authHeader = request.getHeader("Authorization");
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            filterChain.doFilter(request, response);
            return;
        }

        String token = authHeader.substring(7);
        String username = jwtService.extractUsername(token);

        if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
            UserDetails userDetails = userDetailsService.loadUserByUsername(username);
            if (jwtService.isTokenValid(token, userDetails)) {
                UsernamePasswordAuthenticationToken authToken =
                    new UsernamePasswordAuthenticationToken(
                        userDetails, null, userDetails.getAuthorities()
                    );
                authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(authToken);
            }
        }
        filterChain.doFilter(request, response);
    }
}

// JWT service
@Service
public class JwtService {

    @Value("${jwt.secret}")
    private String secretKey;

    public String generateToken(UserDetails userDetails) {
        return Jwts.builder()
            .setSubject(userDetails.getUsername())
            .setIssuedAt(Date.from(Instant.now()))
            .setExpiration(Date.from(Instant.now().plus(Duration.ofHours(24))))
            .signWith(getSigningKey(), SignatureAlgorithm.HS256)
            .compact();
    }

    public String extractUsername(String token) {
        return extractClaim(token, Claims::getSubject);
    }

    public boolean isTokenValid(String token, UserDetails userDetails) {
        String username = extractUsername(token);
        return username.equals(userDetails.getUsername()) && !isTokenExpired(token);
    }
}
```

## Common Mistakes

```java
// WRONG: Hardcoded secret
private String secret = "my-secret-key";  // Never in source code!

// CORRECT: Use application.yml
@Value("${jwt.secret}")
private String secretKey;

// WRONG: No token expiration
Jwts.builder()
    .setSubject(username)
    .signWith(key)  // Token lives forever!
    .compact();

// CORRECT: Set expiration with java.time
Jwts.builder()
    .setSubject(username)
    .setExpiration(Date.from(Instant.now().plus(Duration.ofHours(24))))
    .signWith(key)
    .compact();

// WRONG: Not checking token validity in filter
if (username != null) {
    UserDetails userDetails = userDetailsService.loadUserByUsername(username);
    // Missing isTokenValid() — expired tokens still authenticate!
    UsernamePasswordAuthenticationToken authToken =
        new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
    SecurityContextHolder.getContext().setAuthentication(authToken);
}

// CORRECT: Always validate token before setting authentication
if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
    UserDetails userDetails = userDetailsService.loadUserByUsername(username);
    if (jwtService.isTokenValid(token, userDetails)) {
        UsernamePasswordAuthenticationToken authToken =
            new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
        SecurityContextHolder.getContext().setAuthentication(authToken);
    }
}
```

## Gotchas
- `@EnableWebSecurity` enables Spring Security
- `SessionCreationPolicy.STATELESS` disables sessions
- `addFilterBefore()` inserts JWT filter before authentication
- Use `BCryptPasswordEncoder` for password hashing
- Store secret in environment variables, not source code
- `SecurityContextHolder` stores the authenticated user
- `@PreAuthorize` for method-level security

## Related
- java/spring/boot-basics.md
- java/spring/spring-mvc.md
- crypto/jwt-tokens.md
