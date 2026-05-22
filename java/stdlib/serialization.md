---
id: "java-stdlib-serialization"
title: "JSON Serialization with Jackson and Gson"
language: "java"
category: "stdlib"
tags: ["json", "jackson", "gson", "serialization", "deserialization", "ObjectMapper"]
version: "17+"
retrieval_hint: "json jackson gson serialization deserialization ObjectMapper annotation mapping"
last_verified: "2026-05-22"
confidence: "high"
---

# JSON Serialization with Jackson and Gson

## When to Use
- Converting Java objects to/from JSON (API request/response bodies)
- Reading/writing JSON configuration files
- Serializing objects for caching or message queues
- Parsing JSON from external APIs

## Standard Pattern

```java
import com.fasterxml.jackson.annotation.*;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import java.util.List;
import java.util.Map;

// --- Jackson (most common in Spring) ---
public class JacksonExample {
    private static final ObjectMapper mapper = createMapper();

    private static ObjectMapper createMapper() {
        ObjectMapper m = new ObjectMapper();
        m.registerModule(new JavaTimeModule());
        m.configure(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS, false);
        m.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        return m;
    }

    // Serialize to JSON string
    public static String toJson(Object obj) throws Exception {
        return mapper.writeValueAsString(obj);
    }

    // Deserialize from JSON string
    public static <T> T fromJson(String json, Class<T> type) throws Exception {
        return mapper.readValue(json, type);
    }

    // Deserialize generic types
    public static List<User> readUserList(String json) throws Exception {
        return mapper.readValue(json, new TypeReference<List<User>>() {});
    }
}

// --- Jackson annotations ---
@JsonIgnoreProperties(ignoreUnknown = true)
public record User(
    @JsonProperty("user_id") Long id,
    String name,
    @JsonProperty("email_address") String email,
    @JsonIgnore String password,
    @JsonFormat(pattern = "yyyy-MM-dd") LocalDate createdAt
) {}

// --- Usage ---
String json = JacksonExample.toJson(new User(1L, "Alice", "alice@example.com", "secret", LocalDate.now()));
User user = JacksonExample.fromJson(json, User.class);
List<User> users = JacksonExample.readUserList(jsonArray);

// --- Gson (Google, simpler API) ---
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

Gson gson = new GsonBuilder()
    .setPrettyPrinting()
    .setDateFormat("yyyy-MM-dd")
    .create();

String json = gson.toJson(user);
User user = gson.fromJson(json, User.class);
```

## Common Mistakes

```java
// WRONG: Creating ObjectMapper per request (expensive!)
public String convert(Object obj) {
    ObjectMapper mapper = new ObjectMapper();  // Created every call!
    return mapper.writeValueAsString(obj);
}

// CORRECT: Reuse singleton ObjectMapper
private static final ObjectMapper mapper = new ObjectMapper();

// WRONG: Not handling unknown JSON fields
// {"id": 1, "name": "Alice", "extra_field": "value"}
// Throws UnrecognizedPropertyException!

// CORRECT: Ignore unknown properties
mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
// Or on class: @JsonIgnoreProperties(ignoreUnknown = true)

// WRONG: Exposing internal field names
public record User(Long id, String passwordHash) {}  // "passwordHash" in JSON

// CORRECT: Use @JsonProperty
public record User(Long id, @JsonIgnore String passwordHash) {}

// WRONG: Not handling null values
mapper.writeValueAsString(user);  // Includes "email": null

// CORRECT: Configure null handling
mapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);

// WRONG: Date as timestamp
// "createdAt": 1705334400000  // Not human-readable

// CORRECT: ISO date format
mapper.registerModule(new JavaTimeModule());
mapper.configure(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS, false);
```

## Gotchas
- `ObjectMapper` is thread-safe after configuration — create once, reuse everywhere
- Jackson uses getters for serialization; Gson uses fields — different behavior for inheritance
- `@JsonIgnore` prevents serialization AND deserialization — use `@JsonProperty(access = READ_ONLY)` for write-only
- Jackson's `TypeReference` captures generic types at runtime — required for `List<User>`, `Map<String, User>`
- Gson doesn't support Java records out of the box — use Jackson for records
- `FAIL_ON_UNKNOWN_PROPERTIES = false` is important for forward compatibility — new fields won't break old code
- `JavaTimeModule` is required for `LocalDate`, `LocalDateTime` serialization in Jackson

## Related
- java/spring/spring-mvc.md
- java/stdlib/exception-handling.md
