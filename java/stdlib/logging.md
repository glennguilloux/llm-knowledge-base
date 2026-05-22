---
id: "java-stdlib-logging"
title: "Logging with SLF4J and Logback"
language: "java"
category: "stdlib"
tags: ["logging", "SLF4J", "Logback", "logger", "structured", "MDC"]
version: "17+"
retrieval_hint: "logging SLF4J Logback logger MDC structured log level"
last_verified: "2026-05-22"
confidence: "high"
---

# Logging with SLF4J and Logback

## When to Use
- Adding structured logging to Java applications
- Replacing `System.out.println` with proper log levels
- Correlating logs across requests (MDC)
- Configuring log output format and destinations

## Standard Pattern

```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

public class UserService {
    // Always get logger per class
    private static final Logger log = LoggerFactory.getLogger(UserService.class);

    public User findById(long id) {
        // Use parameterized logging (no string concatenation)
        log.info("Looking up user id={}", id);

        try {
            User user = repository.findById(id);
            log.debug("Found user: {}", user.getName());
            return user;
        } catch (NotFoundException e) {
            log.warn("User not found: id={}", id);
            throw e;
        } catch (Exception e) {
            // Always pass exception as last argument
            log.error("Failed to fetch user id={}", id, e);
            throw e;
        }
    }

    // MDC for request correlation
    public void processRequest(String requestId, String userId) {
        try {
            MDC.put("requestId", requestId);
            MDC.put("userId", userId);
            log.info("Processing request");
            // All subsequent logs include requestId and userId
        } finally {
            MDC.clear();  // Always clear MDC
        }
    }
}

// --- Logback configuration (logback.xml) ---
/*
<configuration>
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <appender name="FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>logs/app.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>logs/app.%d{yyyy-MM-dd}.log</fileNamePattern>
            <maxHistory>30</maxHistory>
        </rollingPolicy>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <root level="INFO">
        <appender-ref ref="STDOUT"/>
        <appender-ref ref="FILE"/>
    </root>
</configuration>
*/
```

## Common Mistakes

```java
// WRONG: String concatenation in log calls
log.info("User " + userId + " logged in from " + ip);  // Always evaluates!

// CORRECT: Parameterized logging (lazy evaluation)
log.info("User {} logged in from {}", userId, ip);  // Only formats if level enabled

// WRONG: Using System.out.println
System.out.println("User logged in: " + userId);  // No level, no format, no file

// CORRECT: Use SLF4J
log.info("User logged in: {}", userId);

// WRONG: Logging sensitive data
log.info("User password: {}", password);  // Security risk!
log.info("Credit card: {}", ccNumber);

// CORRECT: Mask sensitive data
log.info("User login attempt for user={}", userId);
log.info("Payment processed, last4={}", ccNumber.substring(ccNumber.length() - 4));

// WRONG: Not passing exception to logger
catch (Exception e) {
    log.error("Failed: " + e.getMessage());  // Stack trace lost!
}

// CORRECT: Pass exception as last argument
catch (Exception e) {
    log.error("Failed to process request", e);  // Full stack trace

// WRONG: Using wrong log level
log.error("User not found");  // Not an error — it's expected
log.debug("Server starting");  // Important info at debug level

// CORRECT: Use appropriate levels
log.warn("User not found: id={}", id);  // Expected but notable
log.info("Server starting on port {}", port);  // Important operational info
```

## Gotchas
- Parameterized logging (`{}`) is critical for performance — string concatenation happens even if the level is disabled
- Always pass the exception as the LAST argument to the logger — SLF4J treats the last `Throwable` specially
- MDC (Mapped Diagnostic Context) is thread-local — use try/finally to clean up
- `log.isInfoEnabled()` is rarely needed — parameterized logging handles this
- Logback is the default SLF4J implementation in Spring Boot; Log4j2 is an alternative
- `%logger{36}` abbreviates the logger name to 36 characters for compact output
- Rolling file appenders prevent log files from growing unbounded

## Related
- java/spring/boot-basics.md
- java/stdlib/exception-handling.md
