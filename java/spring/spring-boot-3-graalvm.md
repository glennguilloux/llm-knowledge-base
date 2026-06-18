---
id: "java-spring-spring-boot-3-graalvm"
title: "Spring Boot 3 with GraalVM Native Image"
language: "java"
category: "web"
subcategory: "framework"
tags: ["spring-boot", "graalvm", "native-image", "aot", "spring-boot3", "buildpacks", "startup-time"]
version: "17+"
retrieval_hint: "Spring Boot 3 GraalVM native image AOT compilation buildpacks startup optimization reflection"
last_verified: "2026-05-25"
confidence: "high"
---

# Spring Boot 3 with GraalVM Native Image

## When to Use
- Serverless deployments (AWS Lambda, Google Cloud Functions) where cold start matters
- Containerized microservices where image size and startup time are critical
- CLIs and tools built with Spring that need instant startup
- Edge deployments with constrained resources (IoT, small VMs)
- NOT when you need dynamic classloading, CGLIB proxies, or deep runtime reflection

## Standard Pattern

```java
// --- Build configuration: Maven ---
/*
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.2.0</version>
</parent>

<build>
    <plugins>
        <plugin>
            <groupId>org.graalvm.buildtools</groupId>
            <artifactId>native-maven-plugin</artifactId>
        </plugin>
        <plugin>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-maven-plugin</artifactId>
        </plugin>
    </plugins>
</build>
*/

// Build commands:
//   mvn -Pnative native:compile    # Linux native binary
//   mvn spring-boot:build-image    # OCI container with buildpacks

// --- Gradle ---
/*
plugins {
    id 'org.springframework.boot' version '3.2.0'
    id 'io.spring.dependency-management' version '1.1.4'
    id 'org.graalvm.buildtools.native' version '0.10.1'
}
*/

// Build commands:
//   ./gradlew nativeCompile           # Linux native binary
//   ./gradlew bootBuildImage          # OCI container

// --- Application: AOT-friendly patterns ---
import org.springframework.aot.hint.annotation.RegisterReflectionForBinding;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Service;

@SpringBootApplication
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

    @Bean
    MyService myService() {
        return new MyService();
    }
}

// --- Reflection hints for native image ---
// Classes accessed via reflection MUST be registered
@RegisterReflectionForBinding({
    User.class,
    Order.class,
    PaymentDetails.class
})
@Service
public class UserService {
    // Jackson serialization works IF reflection hints are registered
    public String toJson(User user) {
        return new com.fasterxml.jackson.databind.ObjectMapper()
            .writeValueAsString(user);
    }
}

// --- Conditional on AOT phase ---
import org.springframework.aot.AotDetector;

@Service
public class ConfigService {
    public ConfigService() {
        if (AotDetector.useGeneratedArtifacts()) {
            // Running in native image — AOT-generated code is active
            System.out.println("AOT compilation detected");
        }
    }
}
```

## Common Mistakes

```java
// WRONG: Dynamic classloading (not supported in native image)
@Service
public class BadDynamicLoading {
    public void loadPlugin(String className) throws Exception {
        Class<?> clazz = Class.forName(className);  // FAILS in native image!
        Object instance = clazz.getDeclaredConstructor().newInstance();
    }
}

// CORRECT: Use compile-time known types with reflection hints
@RegisterReflectionForBinding(PluginA.class)
@Service
public class GoodPluginLoader {
    public void runPlugin(PluginType type) {
        switch (type) {
            case A -> new PluginA().execute();
            case B -> new PluginB().execute();
        }
    }
}

// WRONG: Expecting all Spring Boot features to work in native mode
// Features with LIMITED native support:
// - spring-boot-devtools (not supported)
// - @ConfigurationProperties on interfaces (use classes)
// - Groovy-based configuration (not supported)
// - JMX (disabled by default)
// - Spring Session JDBC (may need extra hints)

// WRONG: Using proxies without bean hints
// CGLIB proxies for @Configuration classes work (native compiles them).
// BUT dynamic proxies (Proxy.newProxyInstance) need hints:
// @RegisterReflectionForBinding or hints in META-INF/native-image/

// WRONG: Unused ConditionalOnClass that triggers classpath scanning
// Classpath scanning works but is SLOW in native image.
// Each scanned class is additional AOT compilation work.

// CORRECT: Be explicit about what to scan
@SpringBootApplication(scanBasePackages = "com.app")

// CORRECT: Provide reflection hints via RuntimeHintsRegistrar
// For Jackson serialization, dynamic proxy usage, or any reflection.
@Component
public class MyRuntimeHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader cl) {
        hints.reflection()
            .registerType(MyDto.class, MemberCategory.INVOKE_PUBLIC_METHODS);
        hints.proxies()
            .registerJdkProxy(MyInterface.class);
        hints.serialization()
            .registerType(MySerializable.class);
    }
}
```

## Gotchas
- **Serialization differences in native image:** Jackson works but requires reflection hints for all serialized types. `@RegisterReflectionForBinding` or the `org.springframework.aot.hint` API are required. Without hints, Jackson returns empty objects silently.
- **Build time vs runtime:** `@ConditionalOnClass` is evaluated at BUILD TIME during AOT processing. If a class is on the build classpath but you don't want it in the native image, it may still trigger conditionals. Use `RuntimeHintsRegistrar` for runtime-only conditions.
- **Resource scanning is limited:** `SpringFactoriesLoader` and `META-INF/spring/*.imports` are processed at build time. If you add new files to `META-INF/spring/` after the build, they are NOT picked up. Rebuild to pick up changes.
- **Configuration properties need `@ConfigurationPropertiesScan`:** Unlike regular Spring Boot where `@ConfigurationProperties` on beans is auto-detected via classpath scanning, native images need explicit scanning. Add `@ConfigurationPropertiesScan` to your `@SpringBootApplication` class.
- **Testing native images:** Use `-PnativeTest` (Maven) or `nativeTest` (Gradle) to run tests as native images. Not all test infrastructure works — `@SpringBootTest` with `webEnvironment = RANDOM_PORT` is supported, but `MockBean` is NOT (use `@MockitoBean` or `@TestBean` instead).

## Related
- java/spring/boot-basics.md
