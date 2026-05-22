---
id: "java-spring-boot-caching"
title: "Spring Boot Caching with @Cacheable"
language: "java"
category: "web"
subcategory: "caching"
tags: ["spring", "boot", "cache", "cacheable", "evict", "redis", "ehcache"]
version: "17+"
retrieval_hint: "Spring Boot Cacheable CachePut CacheEvict caching Redis EhCache"
last_verified: "2026-05-22"
confidence: "high"
---

# Spring Boot Caching with @Cacheable

## When to Use
- Caching expensive database queries or API calls
- Reducing load on frequently-accessed endpoints
- In-memory caching for configuration data or reference tables
- Distributed caching with Redis for multi-instance deployments

## Standard Pattern

```java
// --- Enable caching ---
@SpringBootApplication
@EnableCaching
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}

// --- Cached service ---
@Service
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }

    // Cache result by ID
    @Cacheable(value = "products", key = "#id")
    public Product findById(Long id) {
        simulateSlowQuery();
        return repository.findById(id).orElseThrow();
    }

    // Cache with custom key (SpEL)
    @Cacheable(value = "products", key = "#name + ':' + #category")
    public List<Product> findByNameAndCategory(String name, String category) {
        return repository.findByNameAndCategory(name, category);
    }

    // Cache with conditional logic
    @Cacheable(value = "products", condition = "#id > 100", unless = "#result == null")
    public Product findByIdConditional(Long id) {
        return repository.findById(id).orElse(null);
    }

    // Update cache
    @CachePut(value = "products", key = "#product.id")
    public Product update(Product product) {
        return repository.save(product);
    }

    // Evict (remove from cache)
    @CacheEvict(value = "products", key = "#id")
    public void delete(Long id) {
        repository.deleteById(id);
    }

    // Evict all entries
    @CacheEvict(value = "products", allEntries = true)
    public void clearCache() {
        // Clears entire "products" cache
    }
}

// --- Redis cache configuration ---
@Configuration
public class CacheConfig {
    @Bean
    public RedisCacheManager cacheManager(RedisConnectionFactory factory) {
        RedisCacheConfiguration config = RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(10))
            .serializeKeysWith(
                RedisSerializationContext.SerializationPair.fromSerializer(new StringRedisSerializer()))
            .serializeValuesWith(
                RedisSerializationContext.SerializationPair.fromSerializer(new GenericJackson2JsonRedisSerializer()));

        return RedisCacheManager.builder(factory)
            .cacheDefaults(config)
            .withCacheConfiguration("products", config.entryTtl(Duration.ofMinutes(30)))
            .build();
    }
}
```

## Common Mistakes

```java
// WRONG: Caching methods called from within the same class
@Service
public class ProductService {
    public Product getProduct(Long id) {
        return findById(id);  // Bypasses proxy — NOT cached!
    }

    @Cacheable("products")
    public Product findById(Long id) { ... }
}

// CORRECT: Call cached method through the proxy (inject self or separate service)
@Service
public class ProductService {
    @Autowired
    private ApplicationContext context;

    public Product getProduct(Long id) {
        return context.getBean(ProductService.class).findById(id);  // Through proxy
    }
}

// WRONG: Caching methods with non-serializable return value
@Cacheable("products")
public Product findById(Long id) {
    return new Product(id, "Name", connection);  // Connection can't be serialized
}

// CORRECT: Ensure return value is serializable
@Cacheable("products")
public ProductDTO findById(Long id) {
    Product p = repository.findById(id).orElseThrow();
    return new ProductDTO(p.getId(), p.getName());  // Simple DTO, serializable
}

// WRONG: No TTL configured (cache grows forever)
// Default TTL may be infinite depending on cache provider

// CORRECT: Configure TTL
RedisCacheConfiguration.defaultCacheConfig().entryTtl(Duration.ofMinutes(10))
```

## Gotchas
- `@Cacheable` uses Spring AOP proxies — self-invocation bypasses the cache
- Cache key defaults to method parameters; use `key = "..."` for custom SpEL expressions
- `unless = "#result == null"` prevents caching null results
- `condition = "..."` is evaluated BEFORE method execution; `unless` is evaluated AFTER
- Redis cache requires serialization — use Jackson or Protobuf for values
- `@CacheEvict(beforeInvocation = true)` evicts even if method throws
- `sync = true` prevents cache stampede (only one thread computes, others wait)
- Cache names must match between `@Cacheable(value = "name")` and cache manager config

## Related
- java/spring/boot-basics.md
- java/spring/boot/scheduled.md
- java/spring/spring-data/jpa-repositories.md
