---
id: "java-testing-spring-boot-testing"
title: "Spring Boot Testing Deep Dive"
language: "java"
category: "testing"
subcategory: "integration-testing"
tags: ["spring", "boot", "testing", "webmvctest", "datajpatest", "springboottest"]
version: "17+"
retrieval_hint: "Spring Boot testing WebMvcTest DataJpaTest SpringBootTest MockMvc test slices"
last_verified: "2026-05-22"
confidence: "high"
---

# Spring Boot Testing Deep Dive

## When to Use
- Testing controllers with MockMvc (WebMvcTest — no server started)
- Testing repository layer with real database (DataJpaTest)
- Full integration tests with entire application context (SpringBootTest)
- Choosing the right test slice for focused, fast tests

## Standard Pattern

```java
// --- Controller test (WebMvcTest — slice test) ---
@WebMvcTest(UserController.class)
class UserControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private UserService userService;  // Mock the service layer

    @Test
    void shouldReturnUser() throws Exception {
        given(userService.findById(1L)).willReturn(
            new UserResponse(1L, "Alice", "alice@test.com"));

        mockMvc.perform(get("/api/users/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("Alice"))
            .andExpect(jsonPath("$.email").value("alice@test.com"));
    }

    @Test
    void shouldReturn404WhenNotFound() throws Exception {
        given(userService.findById(99L)).willThrow(new ResourceNotFoundException("User", 99L));

        mockMvc.perform(get("/api/users/99"))
            .andExpect(status().isNotFound());
    }

    @Test
    void shouldCreateUser() throws Exception {
        given(userService.create(any())).willReturn(
            new UserResponse(1L, "Alice", "alice@test.com"));

        mockMvc.perform(post("/api/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"name": "Alice", "email": "alice@test.com"}
                """))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id").value(1));
    }
}

// --- Repository test (DataJpaTest — slice test) ---
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)  // Use real DB
class UserRepositoryTest {
    @Autowired
    private UserRepository userRepository;

    @Test
    void shouldSaveAndFindUser() {
        User user = userRepository.save(new User(null, "Alice", "alice@test.com"));

        assertThat(user.getId()).isNotNull();
        assertThat(userRepository.findByEmail("alice@test.com"))
            .isPresent()
            .get()
            .extracting(User::getName)
            .isEqualTo("Alice");
    }

    @Test
    void shouldFindByNameContaining() {
        userRepository.save(new User(null, "Alice", "alice@test.com"));
        userRepository.save(new User(null, "Bob", "bob@test.com"));

        assertThat(userRepository.findByNameContaining("Ali")).hasSize(1);
    }
}

// --- Full integration test (SpringBootTest) ---
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
class UserIntegrationTest {
    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private UserRepository userRepository;

    @BeforeEach
    void setUp() {
        userRepository.deleteAll();
    }

    @Test
    void shouldCreateAndRetrieveUser() {
        // Create
        ResponseEntity<UserResponse> createResponse = restTemplate.postForEntity(
            "/api/users",
            new CreateUserRequest("Alice", "alice@test.com"),
            UserResponse.class);

        assertThat(createResponse.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        Long userId = createResponse.getBody().id();

        // Retrieve
        ResponseEntity<UserResponse> getResponse = restTemplate.getForEntity(
            "/api/users/" + userId, UserResponse.class);

        assertThat(getResponse.getBody().name()).isEqualTo("Alice");
    }
}
```

## Common Mistakes

```java
// WRONG: Using @SpringBootTest for controller tests (slow)
@SpringBootTest
class UserControllerTest {
    // Loads entire application context — takes 10+ seconds
}

// CORRECT: Use @WebMvcTest for controller-only tests
@WebMvcTest(UserController.class)
class UserControllerTest {
    // Only loads web layer — takes <1 second
}

// WRONG: Not mocking dependencies in @WebMvcTest
@WebMvcTest(UserController.class)
class UserControllerTest {
    @Autowired
    private MockMvc mockMvc;
    // UserService is not loaded — test fails!
}

// CORRECT: Mock the service layer
@WebMvcTest(UserController.class)
class UserControllerTest {
    @MockBean
    private UserService userService;
}

// WRONG: @DataJpaTest using embedded H2 when you need PostgreSQL
@DataJpaTest
class UserRepositoryTest {
    // Uses H2 by default — PostgreSQL-specific queries may fail
}

// CORRECT: Use real PostgreSQL with Testcontainers
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class UserRepositoryTest {
    // Uses the real datasource (from Testcontainers @DynamicPropertySource)
}
```

## Gotchas
- `@WebMvcTest` only loads web layer — services, repositories are NOT loaded
- `@DataJpaTest` uses an embedded database by default — override with `@AutoConfigureTestDatabase`
- `@SpringBootTest` loads everything — use for integration tests, not unit tests
- `@MockBean` replaces the real bean in the application context with a Mockito mock
- `TestRestTemplate` makes real HTTP calls; `MockMvc` simulates them (no server needed)
- `@Transactional` on test methods auto-rolls back — each test starts clean
- Use `@Sql("data.sql")` for loading test data before tests
- `WebEnvironment.RANDOM_PORT` starts a real server on a random port

## Real-World Example

### Full Integration Test: Sliced Test + Testcontainers + MockMvc

```java
@DataJpaTest
@AutoConfigureMockMvc
@Testcontainers
class UserControllerIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private UserRepository userRepository;

    @BeforeEach
    void setUp() {
        userRepository.deleteAll();
    }

    @Test
    @DisplayName("GET /api/users returns paginated list")
    void listUsers() throws Exception {
        // Arrange
        userRepository.saveAll(List.of(
            new User("alice@example.com", "Alice"),
            new User("bob@example.com", "Bob"),
            new User("charlie@example.com", "Charlie")
        ));

        // Act & Assert
        mockMvc.perform(get("/api/users")
                .param("page", "0")
                .param("size", "2")
                .accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.content", hasSize(2)))
            .andExpect(jsonPath("$.content[0].name").value("Alice"))
            .andExpect(jsonPath("$.totalElements").value(3));
    }

    @Test
    @DisplayName("POST /api/users creates user")
    void createUser() throws Exception {
        mockMvc.perform(post("/api/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"email": "new@example.com", "name": "New User"}
                    """))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id").isNumber())
            .andExpect(jsonPath("$.email").value("new@example.com"));

        assertThat(userRepository.findByEmail("new@example.com")).isPresent();
    }

    @Test
    @DisplayName("POST /api/users with duplicate email returns 409")
    void createUserDuplicate() throws Exception {
        userRepository.save(new User("exists@example.com", "Exists"));

        mockMvc.perform(post("/api/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"email": "exists@example.com", "name": "Duplicate"}
                    """))
            .andExpect(status().isConflict());
    }

    @Test
    @DisplayName("GET /api/users/{id} returns 404 for missing user")
    void getUserNotFound() throws Exception {
        mockMvc.perform(get("/api/users/999"))
            .andExpect(status().isNotFound());
    }
}
```

## Related
- java/testing/mockito-deep.md
- java/testing/testcontainers.md
- java/spring/mvc/controller-advice.md
