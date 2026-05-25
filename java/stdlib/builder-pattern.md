---
id: "java-stdlib-builder-pattern"
title: "Builder, Factory, and Singleton Patterns"
language: "java"
category: "patterns"
tags: ["builder", "factory", "singleton", "design-patterns", "creational", "immutable"]
version: "17+"
retrieval_hint: "builder factory singleton design pattern creational immutable object creation"
last_verified: "2026-05-24"
confidence: "high"
---

# Builder, Factory, and Singleton Patterns

## When to Use
- **Builder**: Constructing complex objects with many optional parameters
- **Factory**: Creating objects without exposing instantiation logic
- **Singleton**: Ensuring a class has exactly one instance

## Standard Pattern

```java
// --- Builder pattern (with Lombok or manual) ---
public class HttpClient {
    private final String baseUrl;
    private final Duration timeout;
    private final int maxRetries;
    private final Map<String, String> headers;

    private HttpClient(Builder builder) {
        this.baseUrl = builder.baseUrl;
        this.timeout = builder.timeout;
        this.maxRetries = builder.maxRetries;
        this.headers = Map.copyOf(builder.headers);
    }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private String baseUrl;
        private Duration timeout = Duration.ofSeconds(10);
        private int maxRetries = 3;
        private Map<String, String> headers = new HashMap<>();

        public Builder baseUrl(String baseUrl) {
            this.baseUrl = baseUrl;
            return this;
        }

        public Builder timeout(Duration timeout) {
            this.timeout = timeout;
            return this;
        }

        public Builder maxRetries(int maxRetries) {
            this.maxRetries = maxRetries;
            return this;
        }

        public Builder header(String key, String value) {
            this.headers.put(key, value);
            return this;
        }

        public HttpClient build() {
            Objects.requireNonNull(baseUrl, "baseUrl is required");
            return new HttpClient(this);
        }
    }
}

// Usage:
// var client = HttpClient.builder()
//     .baseUrl("https://api.example.com")
//     .timeout(Duration.ofSeconds(30))
//     .header("Authorization", "Bearer token")
//     .build();

// --- Factory method ---
public sealed interface Notification permits Email, SMS, Push {
    void send(String recipient, String message);

    static Notification of(String type) {
        return switch (type.toLowerCase()) {
            case "email" -> new Email();
            case "sms" -> new SMS();
            case "push" -> new Push();
            default -> throw new IllegalArgumentException("Unknown type: " + type);
        };
    }
}

// --- Singleton (enum — preferred) ---
public enum AppConfig {
    INSTANCE;

    private final Properties props = loadProperties();

    public String get(String key) {
        return props.getProperty(key);
    }

    private Properties loadProperties() {
        var props = new Properties();
        try (var is = getClass().getResourceAsStream("/app.properties")) {
            props.load(is);
        } catch (Exception e) {
            throw new ExceptionInInitializerError(e);
        }
        return props;
    }
}

// --- Singleton (lazy, thread-safe) ---
public class DatabasePool {
    private static volatile DatabasePool instance;
    private final DataSource dataSource;

    private DatabasePool() {
        this.dataSource = createDataSource();
    }

    public static DatabasePool getInstance() {
        if (instance == null) {
            synchronized (DatabasePool.class) {
                if (instance == null) {
                    instance = new DatabasePool();
                }
            }
        }
        return instance;
    }
}
```

## Common Mistakes

```java
// WRONG: Telescoping constructor
public User(String name) { ... }
public User(String name, String email) { ... }
public User(String name, String email, int age) { ... }
public User(String name, String email, int age, String phone) { ... }
// Hard to read, easy to swap arguments

// CORRECT: Builder pattern
var user = User.builder()
    .name("Alice")
    .email("alice@example.com")
    .age(30)
    .build();

// WRONG: Mutable builder (allows modification after build)
public class Config {
    private String url;
    public void setUrl(String url) { this.url = url; }  // Mutable!
}

// CORRECT: Immutable with builder
public class Config {
    private final String url;
    private Config(Builder b) { this.url = b.url; }
}

// WRONG: Singleton with public constructor
public class Database {
    public Database() { ... }  // Anyone can create instances
}

// CORRECT: Private constructor + factory
public class Database {
    private static final Database INSTANCE = new Database();
    private Database() { ... }
    public static Database getInstance() { return INSTANCE; }
}

// WRONG: Singleton with synchronized (slow every access)
public static synchronized Database getInstance() {
    if (instance == null) instance = new Database();
    return instance;
}

// CORRECT: Double-checked locking with volatile
private static volatile Database instance;
public static Database getInstance() {
    if (instance == null) {
        synchronized (Database.class) {
            if (instance == null) instance = new Database();
        }
    }
    return instance;
}
```

## Gotchas
- Builder pattern is verbose without Lombok — consider `@Builder` annotation
- Immutable objects (records) are preferred over mutable builders when possible
- Enum singletons are the safest and most concise — serialization and reflection are handled
- Factory methods can return subtypes — more flexible than constructors
- `sealed` interfaces (Java 17+) with `permits` give exhaustive pattern matching
- Builder validation should happen in `build()`, not in setter methods
- `Map.copyOf()` creates an immutable snapshot — mutations to the original map don't affect the built object

## Related
- java/stdlib/records.md
- java/stdlib/collections.md
- java/stdlib/exception-handling.md
