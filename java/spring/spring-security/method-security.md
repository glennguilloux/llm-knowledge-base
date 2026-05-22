---
id: "java-spring-security-method-security"
title: "Spring Security Method-Level Security"
language: "java"
category: "web"
subcategory: "security"
tags: ["spring", "spring-security", "preauthorize", "spel", "method-security", "rbac"]
version: "17+"
retrieval_hint: "Spring Security method level @PreAuthorize @PostAuthorize SpEL expression role-based"
last_verified: "2026-05-22"
confidence: "high"
---

# Spring Security Method-Level Security

## When to Use
- Fine-grained authorization beyond URL patterns (e.g., "only the owner can edit")
- Service-layer security checks that depend on method arguments or return values
- Role-based access control (RBAC) at the method level
- Filtering returned collections based on user permissions
- Applications where controller-level security is insufficient

## Standard Pattern

```java
// Enable method security (Spring Security 6+)
@Configuration
@EnableMethodSecurity  // replaces @EnableGlobalMethodSecurity(prePostEnabled = true)
public class MethodSecurityConfig {
    // Optional: register a custom PermissionEvaluator
    @Bean
    public MethodSecurityExpressionHandler methodSecurityExpressionHandler(
            PermissionEvaluator permissionEvaluator) {
        DefaultMethodSecurityExpressionHandler handler = new DefaultMethodSecurityExpressionHandler();
        handler.setPermissionEvaluator(permissionEvaluator);
        return handler;
    }
}

// Service with method-level security
@Service
public class DocumentService {

    @PreAuthorize("hasRole('EDITOR')")
    public Document createDocument(DocumentDto dto) {
        return documentRepository.save(new Document(dto));
    }

    @PreAuthorize("hasRole('ADMIN') or #document.owner == authentication.name")
    public Document updateDocument(Document document) {
        return documentRepository.save(document);
    }

    @PreAuthorize("hasPermission(#id, 'Document', 'read')")
    public Document getDocument(Long id) {
        return documentRepository.findById(id)
            .orElseThrow(() -> new EntityNotFoundException("Document not found"));
    }

    @PreAuthorize("hasRole('ADMIN')")
    @PostFilter("filterObject.owner == authentication.name or hasRole('ADMIN')")
    public List<Document> listAllDocuments() {
        return documentRepository.findAll();
    }

    @PreAuthorize("#document.owner == authentication.name")
    @PreFilter(filterObject = "owner")  // not commonly used — shown for completeness
    public void deleteDocument(Document document) {
        documentRepository.delete(document);
    }

    @PostAuthorize("returnObject.owner == authentication.name or hasRole('ADMIN')")
    public Document getDocumentStrict(Long id) {
        return documentRepository.findById(id)
            .orElseThrow(() -> new EntityNotFoundException("Document not found"));
    }
}

// Custom PermissionEvaluator for hasPermission()
@Component
class DocumentPermissionEvaluator implements PermissionEvaluator {

    private final DocumentRepository documentRepository;

    DocumentPermissionEvaluator(DocumentRepository documentRepository) {
        this.documentRepository = documentRepository;
    }

    @Override
    public boolean hasPermission(
            Authentication authentication, Object targetDomainObject, Object permission) {
        if (targetDomainObject instanceof Document doc) {
            return checkAccess(authentication, doc, (String) permission);
        }
        return false;
    }

    @Override
    public boolean hasPermission(
            Authentication authentication, Serializable targetId, String targetType, Object permission) {
        if ("Document".equals(targetType)) {
            Document doc = documentRepository.findById((Long) targetId).orElse(null);
            return doc != null && checkAccess(authentication, doc, (String) permission);
        }
        return false;
    }

    private boolean checkAccess(Authentication auth, Document doc, String permission) {
        String username = auth.getName();
        boolean isOwner = doc.getOwner().equals(username);
        boolean isAdmin = auth.getAuthorities().stream()
            .anyMatch(a -> a.getAuthority().equals("ROLE_ADMIN"));

        return switch (permission) {
            case "read" -> isOwner || isAdmin;
            case "write", "delete" -> isOwner;
            default -> false;
        };
    }
}
```

## Common Mistakes

```java
// WRONG: Calling a @PreAuthorize method from within the same class
@Service
public class UserService {
    public void doSomething() {
        createUser(dto);  // bypasses security — no proxy interception
    }

    @PreAuthorize("hasRole('ADMIN')")
    public User createUser(UserDto dto) { ... }
}

// CORRECT: Inject the service and call through the proxy
@Service
public class UserFacade {
    private final UserService userService;

    public void doSomething() {
        userService.createUser(dto);  // goes through AOP proxy — security applied
    }
}

// WRONG: Using hasAuthority('ADMIN') instead of hasRole('ADMIN')
@PreAuthorize("hasAuthority('ADMIN')")  // expects granted authority "ADMIN"
// But Spring Security adds "ROLE_" prefix, so the actual authority is "ROLE_ADMIN"

// CORRECT: Use hasRole() for role checks (automatically adds ROLE_ prefix)
@PreAuthorize("hasRole('ADMIN')")

// WRONG: SpEL expression referencing nonexistent method parameter
@PreAuthorize("#userId == authentication.name")  // userId not a parameter!

// CORRECT: Match the SpEL variable to the actual parameter name
@PreAuthorize("#id == authentication.name")
public void deleteUser(Long id) { ... }
```

## Gotchas
- `@EnableMethodSecurity` replaces the deprecated `@EnableGlobalMethodSecurity(prePostEnabled = true)`
- Method security uses AOP proxies — self-invocation (same class) bypasses security
- `@PostFilter` iterates the returned collection in memory — use SQL-level filtering for large datasets
- `@PreFilter` only works on collection parameters; for single objects, use `@PreAuthorize` with SpEL
- SpEL has access to `authentication`, `principal`, `authentication.name`, and `hasRole()` / `hasPermission()`
- `hasRole('ADMIN')` checks for authority `ROLE_ADMIN` — the prefix is added automatically
- `@Secured({"ROLE_ADMIN"})` is older style; prefer `@PreAuthorize` for new code
- Custom `PermissionEvaluator` must be registered as a Spring bean to be picked up by SpEL
- Kotlin data classes may not preserve parameter names — use `-parameters` compiler flag or explicit `@Param`

## Related
- java/spring/spring-security/jwt-auth.md
- java/spring/spring-security/oauth2-setup.md
- java/spring/spring-security/csrf-protection.md
