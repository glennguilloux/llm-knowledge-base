---
id: "java-spring-boot-basics"
title: "Spring Boot Application Setup"
language: "java"
category: "web"
subcategory: "api-framework"
tags: ["spring", "boot", "application", "configuration", "auto-configuration"]
version: "17+"
retrieval_hint: "Spring Boot application configuration auto-configuration"
last_verified: "2026-05-22"
confidence: "high"
---

# Spring Boot Application Setup

## When to Use
- Building REST APIs with Java
- Microservice development
- Auto-configuration of Spring components
- Production-ready applications

## Standard Pattern

```java
// Main application class
package com.example.demo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.bind.annotation.*;

@SpringBootApplication
public class DemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }
}

// Controller
@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping
    public List<User> listUsers() {
        return userService.findAll();
    }

    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id)
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public User createUser(@Valid @RequestBody UserRequest request) {
        return userService.create(request);
    }

    @PutMapping("/{id}")
    public User updateUser(@PathVariable Long id, @Valid @RequestBody UserRequest request) {
        return userService.update(id, request);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteUser(@PathVariable Long id) {
        userService.delete(id);
    }
}

// Service
@Service
@Transactional
public class UserService {
    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public List<User> findAll() {
        return userRepository.findAll();
    }

    public Optional<User> findById(Long id) {
        return userRepository.findById(id);
    }

    public User create(UserRequest request) {
        User user = new User();
        user.setName(request.getName());
        user.setEmail(request.getEmail());
        return userRepository.save(user);
    }
}
```

## Common Mistakes

```java
// WRONG: Using field injection
@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;  // Hard to test!
}

// CORRECT: Use constructor injection
@Service
public class UserService {
    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }
}

// WRONG: Not using @Valid
@PostMapping
public User createUser(@RequestBody UserRequest request) {
    // No validation!
    return userService.create(request);
}

// CORRECT: Add @Valid
@PostMapping
public User createUser(@Valid @RequestBody UserRequest request) {
    return userService.create(request);
}
```

## Gotchas
- `@SpringBootApplication` combines `@Configuration`, `@EnableAutoConfiguration`, `@ComponentScan`
- Constructor injection is preferred over field injection
- `@Transactional` on service methods for database transactions
- `@Valid` triggers Bean Validation on request bodies
- `@ResponseStatus` sets the HTTP status code
- Use `application.yml` or `application.properties` for configuration
- `@CrossOrigin` for CORS configuration

## Related
- java/spring/spring-mvc.md
- java/spring/spring-data/jpa-repositories.md
- java/spring/spring-security/jwt-auth.md
