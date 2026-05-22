---
id: "java-spring-data-transactions"
title: "Spring Data JPA Transactions"
language: "java"
category: "db"
subcategory: "transactions"
tags: ["spring", "data", "jpa", "transaction", "rollback", "isolation"]
version: "17+"
retrieval_hint: "Spring Data JPA transaction rollback isolation propagation"
last_verified: "2026-05-22"
confidence: "high"
---

# Spring Data JPA Transactions

## When to Use
- Multi-step database operations that must be atomic
- Read-only queries for performance optimization
- Custom isolation levels
- Rollback on specific exceptions

## Standard Pattern

```java
// Service with transactional methods
@Service
public class OrderService {

    private final OrderRepository orderRepository;
    private final InventoryService inventoryService;

    public OrderService(OrderRepository orderRepository, InventoryService inventoryService) {
        this.orderRepository = orderRepository;
        this.inventoryService = inventoryService;
    }

    @Transactional
    public Order createOrder(OrderRequest request) {
        // All operations in single transaction
        Order order = new Order();
        order.setCustomerId(request.customerId());
        order.setItems(request.items());
        order = orderRepository.save(order);
        
        inventoryService.reserveStock(order.getItems());
        
        return order;
    }

    @Transactional(readOnly = true)
    public List<Order> findOrders(Long customerId) {
        return orderRepository.findByCustomerId(customerId);
    }

    @Transactional(rollbackFor = InsufficientStockException.class)
    public void processOrder(Long orderId) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new ResourceNotFoundException("Order not found"));
        
        inventoryService.deductStock(order.getItems());
        order.setStatus(OrderStatus.PROCESSED);
        orderRepository.save(order);
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void auditLog(String action) {
        // Runs in new transaction, independent of caller
        auditRepository.save(new AuditEntry(action, LocalDateTime.now()));
    }
}
```

## Common Mistakes

```java
// WRONG: Calling @Transactional method from same class
@Service
public class UserService {
    @Transactional
    public void createUser(UserRequest request) {
        // ...
    }
    
    public void createUsers(List<UserRequest> requests) {
        for (UserRequest request : requests) {
            createUser(request);  // NOT transactional! (proxy bypass)
        }
    }
}

// CORRECT: Move to separate service or use self-injection
@Service
public class UserService {
    @Autowired
    private UserService self;
    
    @Transactional
    public void createUser(UserRequest request) { ... }
    
    public void createUsers(List<UserRequest> requests) {
        for (UserRequest request : requests) {
            self.createUser(request);  // Transactional via proxy
        }
    }
}

// WRONG: Catching exceptions prevents rollback
@Transactional
public void process() {
    try {
        riskyOperation();
    } catch (Exception e) {
        log.error("Error", e);  // Transaction commits!
    }
}

// CORRECT: Let exceptions propagate or mark for rollback
@Transactional
public void process() {
    riskyOperation();  // Exception propagates, transaction rolls back
}
```

## Gotchas
- `@Transactional` creates a proxy — self-invocation bypasses it
- `readOnly = true` optimizes for read queries (no dirty checking)
- Default rollback: unchecked exceptions; use `rollbackFor` for checked
- `REQUIRES_NEW` suspends current transaction and creates new one
- `NESTED` creates savepoint for partial rollback
- Place `@Transactional` on service methods, not repository methods
- Use `@Transactional(noRollbackFor = ExpectedException.class)` to prevent rollback

## Related
- java/spring/spring-data/jpa-repositories.md
- java/spring/spring-data/queries.md
- java/spring/boot-basics.md
