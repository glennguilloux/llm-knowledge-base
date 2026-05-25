---
id: "java-testing-mockito-deep"
title: "Mockito Deep Dive: Mocking, Stubbing, and Verification"
language: "java"
category: "testing"
subcategory: "unit-testing"
tags: ["mockito", "mock", "stub", "verify", "argument-captor", "spy"]
version: "17+"
retrieval_hint: "Mockito mock stub verify argument captor spy when then BDD"
last_verified: "2026-05-24"
confidence: "high"
---

# Mockito Deep Dive: Mocking, Stubbing, and Verification

## When to Use
- Isolating units under test from dependencies (database, HTTP clients, services)
- Verifying interactions between objects (method calls, argument values)
- Testing error handling by stubbing exceptions
- Capturing arguments passed to mocked methods for assertions

## Standard Pattern

```java
import static org.mockito.Mockito.*;
import static org.mockito.BDDMockito.*;
import static org.assertj.core.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private EmailService emailService;

    @InjectMocks
    private UserService userService;

    @Captor
    private ArgumentCaptor<User> userCaptor;

    @Test
    void shouldCreateUser() {
        // Given (BDD style)
        User savedUser = new User(1L, "Alice", "alice@test.com");
        given(userRepository.save(any(User.class))).willReturn(savedUser);

        // When
        User result = userService.create("Alice", "alice@test.com");

        // Then
        assertThat(result.getId()).isEqualTo(1L);
        assertThat(result.getName()).isEqualTo("Alice");
        then(userRepository).should().save(any(User.class));
    }

    @Test
    void shouldThrowWhenUserExists() {
        // Given
        given(userRepository.findByEmail("alice@test.com"))
            .willReturn(Optional.of(new User()));

        // When / Then
        assertThatThrownBy(() -> userService.create("Alice", "alice@test.com"))
            .isInstanceOf(DuplicateEmailException.class)
            .hasMessageContaining("alice@test.com");
    }

    @Test
    void shouldCaptureSavedUser() {
        // Given
        given(userRepository.save(any(User.class))).willAnswer(inv -> inv.getArgument(0));

        // When
        userService.create("Alice", "alice@test.com");

        // Then
        then(userRepository).should().save(userCaptor.capture());
        User captured = userCaptor.getValue();
        assertThat(captured.getName()).isEqualTo("Alice");
        assertThat(captured.getEmail()).isEqualTo("alice@test.com");
    }

    @Test
    void shouldVerifyEmailSentOnce() {
        // Given
        given(userRepository.save(any(User.class))).willReturn(new User(1L, "Alice", "a@b.com"));

        // When
        userService.create("Alice", "alice@test.com");

        // Then
        then(emailService).should(only()).sendWelcomeEmail("alice@test.com");
        then(emailService).shouldHaveNoMoreInteractions();
    }

    @Test
    void shouldStubMultipleCalls() {
        // First call returns empty, second returns the user
        given(userRepository.findById(1L))
            .willReturn(Optional.empty())
            .willReturn(Optional.of(new User(1L, "Alice", "a@b.com")));

        assertThat(userService.findById(1L)).isNull();  // First call
        assertThat(userService.findById(1L)).isNotNull();  // Second call
    }

    // Spy: partial mock (real object with selective overrides)
    @Test
    void shouldSpyOnRealObject() {
        List<String> list = new ArrayList<>(List.of("a", "b"));
        List<String> spy = spy(list);

        doReturn("c").when(spy).get(2);  // Override specific method
        assertThat(spy.get(2)).isEqualTo("c");
        assertThat(spy).hasSize(2);  // Real behavior
    }
}
```

## Common Mistakes

```java
// WRONG: Using when().thenReturn() on void methods
when(emailService.send(any())).thenReturn(null);  // Compilation error for void!

// CORRECT: Use doNothing() or doThrow() for void methods
doNothing().when(emailService).send(any());
doThrow(new EmailException("Failed")).when(emailService).send(any());

// WRONG: Mocking value objects / data classes
@Mock
private User user;  // Don't mock what you own — just create it

// CORRECT: Use real objects for simple data
User user = new User(1L, "Alice", "alice@test.com");

// WRONG: Verifying implementation details
verify(userRepository).save(userCaptor.capture());
verify(userRepository).flush();  // Testing HOW, not WHAT

// CORRECT: Verify behavior/outcome
then(userRepository).should().save(any());
// Don't verify internal calls unless they're part of the contract

// WRONG: Argument matcher mixed with raw values
when(userRepository.findByNameAndEmail(eq("Alice"), "alice@test.com"))
// Raw values can't be mixed with matchers!

// CORRECT: Use matchers for all args or none
when(userRepository.findByNameAndEmail(eq("Alice"), eq("alice@test.com")))
```

## Gotchas
- `@Mock` creates mocks; `@InjectMocks` creates the class and injects mocks into it
- `@Captor` captures arguments for later assertions
- BDD style (`given().willReturn()`) reads more naturally than `when().thenReturn()`
- `any()` matches any value including null; `any(Class.class)` matches non-null of that type
- `verify(mock, times(2))` checks exact call count; `atLeastOnce()`, `never()` are alternatives
- `spy()` wraps a real object — use `doReturn()` instead of `when()` to avoid calling the real method
- `@ExtendWith(MockitoExtension.class)` is needed for JUnit 5 (replaces `@RunWith(MockitoJUnitRunner.class)`)
- Mocks return defaults: `null` for objects, `0` for numbers, `false` for booleans

## Related
- java/testing/spring-boot-testing.md
- java/testing/testcontainers.md
- java/spring/spring-data/jpa-repositories.md
