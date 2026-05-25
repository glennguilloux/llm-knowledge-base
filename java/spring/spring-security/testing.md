---
id: "java-spring-security-testing"
title: "Testing Spring Security"
language: "java"
category: "web"
subcategory: "testing"
tags: ["spring", "spring-security", "testing", "mock-user", "integration-test", "mockmvc"]
version: "17+"
retrieval_hint: "Spring Security testing @WithMockUser @WithUserDetails MockMvc security context"
last_verified: "2026-05-24"
confidence: "high"
---

# Testing Spring Security

## When to Use
- Unit or integration testing controllers secured with `@PreAuthorize`, `@Secured`, or URL rules
- Verifying that unauthorized users get 403/401 responses
- Testing permission logic without a real identity provider
- Simulating authenticated requests in MockMvc or WebTestClient tests

## Standard Pattern

```java
// --- Controller under test ---
@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping("/me")
    public UserDto getCurrentUser(@AuthenticationPrincipal Jwt jwt) {
        return userService.findBySub(jwt.getSubject());
    }

    @PreAuthorize("hasRole('ADMIN')")
    @GetMapping
    public List<UserDto> listUsers() {
        return userService.findAll();
    }

    @PreAuthorize("#id == authentication.name or hasRole('ADMIN')")
    @GetMapping("/{id}")
    public UserDto getUser(@PathVariable String id) {
        return userService.findById(id);
    }
}

// --- MockMvc tests with @WithMockUser ---
@WebMvcTest(UserController.class)
class UserControllerMockMvcTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private UserService userService;

    @Test
    @WithMockUser(roles = "ADMIN")
    void listUsers_asAdmin_returnsOk() throws Exception {
        mockMvc.perform(get("/api/users"))
            .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(roles = "USER")
    void listUsers_asUser_returnsForbidden() throws Exception {
        mockMvc.perform(get("/api/users"))
            .andExpect(status().isForbidden());
    }

    @Test
    void listUsers_unauthenticated_returnsUnauthorized() throws Exception {
        mockMvc.perform(get("/api/users"))
            .andExpect(status().isUnauthorized());
    }
}

// --- @WithMockUser customization ---
@Test
@WithMockUser(
    username = "alice",
    roles = {"USER", "EDITOR"},
    password = "unused"  // required field, not used in tests
)
void testWithCustomUser() { ... }

// --- @WithUserDetails (loads from UserDetailsService) ---
@Test
@WithUserDetails(
    value = "alice",
    userDetailsServiceBeanName = "customUserDetailsService"
)
void testWithRealUserDetails() { ... }

// --- @WithAnonymousUser ---
@Test
@WithAnonymousUser
void anonymousUser_redirectedToLogin() throws Exception {
    mockMvc.perform(get("/dashboard"))
        .andExpect(status().is3xxRedirection());
}

// --- SecurityMockMvcRequestPostProcessors (more control) ---
@Test
void customJwtToken() throws Exception {
    Jwt jwt = Jwt.withTokenValue("test-token")
        .header("alg", "none")
        .claim("sub", "alice")
        .claim("roles", List.of("ADMIN"))
        .build();

    mockMvc.perform(get("/api/users/me")
            .with(jwt().jwt(jwt)))
        .andExpect(status().isOk());
}

@Test
void csrfTokenRequired() throws Exception {
    mockMvc.perform(post("/api/data")
            .with(csrf()))   // adds valid CSRF token
        .andExpect(status().isOk());
}

@Test
void noCsrf_returnsForbidden() throws Exception {
    mockMvc.perform(post("/api/data"))  // no CSRF token
        .andExpect(status().isForbidden());
}

// --- Integration test with full context ---
@SpringBootTest
@AutoConfigureMockMvc
class UserApiIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @WithMockUser(username = "admin", roles = "ADMIN")
    void adminCanListUsers() throws Exception {
        mockMvc.perform(get("/api/users"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$").isArray());
    }

    @Test
    @WithMockUser(username = "alice", roles = "USER")
    void userCannotAccessOtherUsers() throws Exception {
        mockMvc.perform(get("/api/users/bob"))
            .andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(username = "alice", roles = "USER")
    void userCanAccessOwnProfile() throws Exception {
        mockMvc.perform(get("/api/users/alice"))
            .andExpect(status().isOk());
    }
}

// --- Testing with WebTestClient (reactive or MVC) ---
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class UserApiWebTestClientTest {

    @Autowired
    private WebTestClient webTestClient;

    @Test
    void authenticatedRequest() {
        webTestClient
            .mutateWith(SecurityMockMvcConfigurers.mockUser("alice").roles("USER"))
            .get().uri("/api/users/me")
            .exchange()
            .expectStatus().isOk();
    }
}
```

## Common Mistakes

```java
// WRONG: Using @WithMockUser on a @SpringBootTest without @AutoConfigureMockMvc
@SpringBootTest
class MyTest {
    @Autowired MockMvc mockMvc;  // Not auto-configured — NullPointerException

    @Test @WithMockUser
    void test() { ... }
}

// CORRECT: Add @AutoConfigureMockMvc
@SpringBootTest
@AutoConfigureMockMvc
class MyTest {
    @Autowired MockMvc mockMvc;  // Now properly injected

    @Test @WithMockUser
    void test() { ... }
}

// WRONG: Testing @PreAuthorize without enabling method security in test context
@WebMvcTest(UserController.class)  // @EnableMethodSecurity not loaded by @WebMvcTest
class UserTest {
    @Test @WithMockUser(roles = "ADMIN")
    void test() { ... }  // @PreAuthorize not evaluated — test passes incorrectly
}

// CORRECT: Import the security configuration
@WebMvcTest(UserController.class)
@Import(MethodSecurityConfig.class)  // ensures @EnableMethodSecurity is active
class UserTest { ... }

// WRONG: Testing secured endpoint without any authentication annotation
@WebMvcTest(UserController.class)
class UserTest {
    @Test
    void listUsers_shouldReturnOk() throws Exception {
        mockMvc.perform(get("/api/users"))
            .andExpect(status().isOk());  // Fails: 401 Unauthorized
    }
}

// CORRECT: Add @WithMockUser for authenticated tests
@WebMvcTest(UserController.class)
@Import(MethodSecurityConfig.class)
class UserTest {
    @Test
    @WithMockUser(roles = "ADMIN")
    void listUsers_asAdmin_shouldReturnOk() throws Exception {
        mockMvc.perform(get("/api/users"))
            .andExpect(status().isOk());
    }
}
```

## Gotchas
- `@WithMockUser` creates a mock `Authentication` in the `SecurityContextHolder` — no `UserDetailsService` call
- `@WithUserDetails` actually calls your `UserDetailsService` — use when you need real user data
- `@WebMvcTest` does NOT load `@EnableMethodSecurity` by default — import the config class explicitly
- `SecurityMockMvcRequestPostProcessors.jwt()` is in `spring-security-test` dependency
- The `roles` parameter in `@WithMockUser` automatically adds `ROLE_` prefix — `roles = "ADMIN"` grants authority `ROLE_ADMIN`
- `@WithMockUser` works on individual test methods AND on the class (applies to all tests)
- For testing CSRF with `MockMvc`, always add `.with(csrf())` on POST/PUT/DELETE requests
- `@Transactional` on tests rolls back after each test — useful for DB-dependent security tests
- When testing with `@SpringBootTest`, the full security filter chain runs — match production behavior

## Related
- java/spring/spring-security/jwt-auth.md
- java/testing/spring-boot-testing.md
- java/spring/spring-security/method-security.md
