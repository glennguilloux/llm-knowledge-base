---
id: "java-testing-junit5"
title: "JUnit 5 Testing"
language: "java"
category: "testing"
subcategory: "unit-testing"
tags: ["junit", "testing", "assertions", "parameterized", "mockito"]
version: "17+"
retrieval_hint: "JUnit 5 testing assertions parameterized mockito"
last_verified: "2026-05-24"
confidence: "high"
---

# JUnit 5 Testing

## When to Use
- Unit testing Java applications
- Parameterized tests
- Test lifecycle management
- Integration with Spring Boot

## Standard Pattern

```java
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class CalculatorTest {

    private Calculator calculator;

    @BeforeEach
    void setUp() {
        calculator = new Calculator();
    }

    @Test
    void shouldAddNumbers() {
        assertEquals(5, calculator.add(2, 3));
    }

    @Test
    void shouldThrowOnDivisionByZero() {
        assertThrows(ArithmeticException.class, () -> calculator.divide(1, 0));
    }

    @Test
    void shouldHandleNullInput() {
        assertNull(calculator.parse(null));
    }

    @ParameterizedTest
    @CsvSource({
        "1, 1, 2",
        "2, 3, 5",
        "0, 0, 0",
        "-1, 1, 0"
    })
    void shouldAddVariousNumbers(int a, int b, int expected) {
        assertEquals(expected, calculator.add(a, b));
    }

    @ParameterizedTest
    @ValueSource(ints = {2, 4, 6, 8})
    void shouldIdentifyEvenNumbers(int number) {
        assertTrue(calculator.isEven(number));
    }

    @Test
    @DisplayName("Should calculate compound interest correctly")
    void compoundInterest() {
        double result = calculator.compoundInterest(1000, 0.05, 12, 1);
        assertEquals(1051.16, result, 0.01);
    }

    @Test
    @Disabled("Implement when feature X is ready")
    void futureFeature() {
        // TODO
    }
}

// Mockito integration
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @Test
    void shouldFindUserById() {
        User user = new User(1L, "Alice");
        when(userRepository.findById(1L)).thenReturn(Optional.of(user));

        Optional<User> result = userService.findById(1L);

        assertTrue(result.isPresent());
        assertEquals("Alice", result.get().getName());
        verify(userRepository).findById(1L);
    }

    @Test
    void shouldThrowWhenUserNotFound() {
        when(userRepository.findById(99L)).thenReturn(Optional.empty());

        assertThrows(ResourceNotFoundException.class, 
            () -> userService.findById(99L));
    }
}
```

## Common Mistakes

```java
// WRONG: Testing multiple things
@Test
void testUser() {
    User user = new User("Alice");
    assertEquals("Alice", user.getName());
    assertTrue(user.isActive());
    assertNotNull(user.getCreatedAt());
    // Too many assertions!

// CORRECT: One assertion per test
@Test
void shouldSetName() {
    User user = new User("Alice");
    assertEquals("Alice", user.getName());
}

// WRONG: Not using @BeforeEach for setup
@Test
void test1() {
    Calculator calc = new Calculator();  // Repeated!
    // ...
}

@Test
void test2() {
    Calculator calc = new Calculator();  // Repeated!
    // ...
}

// CORRECT: Use @BeforeEach
@BeforeEach
void setUp() {
    calculator = new Calculator();
}

// WRONG: Using Mockito annotations without @ExtendWith
class UserServiceTest {
    @Mock
    private UserRepository userRepository;  // Null — annotations not processed

    @InjectMocks
    private UserService userService;

    @Test
    void shouldFindUser() {
        when(userRepository.findById(1L)).thenReturn(Optional.empty());  // NullPointerException
    }
}

// CORRECT: Add @ExtendWith(MockitoExtension.class)
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @Test
    void shouldFindUser() {
        when(userRepository.findById(1L)).thenReturn(Optional.empty());
        assertThrows(ResourceNotFoundException.class, () -> userService.findById(1L));
    }
}
```

## Gotchas
- `@BeforeEach` runs before each test; `@BeforeAll` runs once (must be static)
- `assertThrows()` returns the exception for further assertions
- `assertEquals(expected, actual, delta)` for floating-point comparison
- `@ParameterizedTest` replaces `@Test` for parameterized tests
- `@ExtendWith(MockitoExtension.class)` enables Mockito annotations
- `@Mock` creates mock; `@InjectMocks` injects mocks into target
- `verify()` checks method was called; `verifyNoInteractions()` checks it wasn't

## Related
- java/spring/boot-basics.md
- java/spring/spring-data/jpa-repositories.md
