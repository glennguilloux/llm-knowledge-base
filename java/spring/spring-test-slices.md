---
id: "java-spring-test-slices"
title: "Spring Boot Test Slices"
language: "java"
category: "web"
subcategory: "testing"
tags: ["spring-boot", "testing", "DataJpaTest", "WebMvcTest", "JsonTest", "SpringBootTest", "MockMvc", "slicing"]
version: "17+"
retrieval_hint: "Spring Boot test slices DataJpaTest WebMvcTest JsonTest SpringBootTest MockMvc repository controller JSON"
last_verified: "2026-06-20"
confidence: "medium"
---

# Spring Boot Test Slices

## When to Use
- Testing repository behavior without starting the full application context.
- Testing MVC controllers with `MockMvc` and mocked services.
- Testing JSON serialization and deserialization independently from HTTP handling.
- Reserving `@SpringBootTest` for true integration scenarios where slicing is not enough.

## Standard Pattern

```java
package com.example.catalog.test;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.json.JacksonTester;
import org.springframework.boot.test.autoconfigure.json.JsonTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;

@DataJpaTest
class OrderRepositorySliceTest {

    @Autowired
    OrderRepository orders;

    @Test
    void findsOpenOrdersByCustomer() {
        orders.save(new Order("customer-a", OrderStatus.OPEN));

        List<Order> openOrders = orders.findByCustomerIdAndStatus("customer-a", OrderStatus.OPEN);

        assertThat(openOrders).hasSize(1);
    }
}

@WebMvcTest(OrderController.class)
class OrderControllerSliceTest {

    @Autowired
    MockMvc mockMvc;

    @MockBean
    OrderService orderService;

    @Test
    void returnsCustomerOrders() throws Exception {
        when(orderService.findForCustomer("customer-a"))
            .thenReturn(List.of(new OrderResponse(1L, "OPEN")));

        mockMvc.perform(MockMvcRequestBuilders.get("/api/customers/customer-a/orders"))
            .andExpect(MockMvcResultMatchers.status().isOk())
            .andExpect(MockMvcResultMatchers.jsonPath("$[0].id").value(1));
    }
}

@JsonTest
class OrderResponseJsonSliceTest {

    @Autowired
    JacksonTester<OrderResponse> json;

    @Test
    void serializesOnlyNonNullFields() {
        OrderResponse response = new OrderResponse(1L, "OPEN");

        json.assertThat(response)
            .hasJsonPathNumberValue("@.id")
            .hasJsonPathStringValue("@.status");
    }
}

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.NONE)
class OrderServiceIntegrationTest {

    @Autowired
    OrderService orderService;

    @Test
    void usesFullConfigurationWhenSlicesAreNotEnough() {
        assertThat(orderService).isNotNull();
    }
}
```

## Common Mistakes

```java
// WRONG: Loading the full application context for a simple repository query test.
@SpringBootTest
class OrderRepositoryTest {
}

// CORRECT: Use @DataJpaTest for repository and entity mapping checks.
@DataJpaTest
class OrderRepositoryTest {
}

// WRONG: Using @WebMvcTest when the goal is to test the full embedded server and real filters.
@WebMvcTest(OrderController.class)
class FullServerTest {
}

// CORRECT: Use @SpringBootTest with a random web port for end-to-end web integration tests.
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class FullServerTest {
}

// WRONG: Expecting a service bean inside @DataJpaTest without importing it.
@DataJpaTest
class OrderServiceTest {
    @Autowired
    OrderService service;
}

// CORRECT: Import only the focused service and keep the slice narrow.
@DataJpaTest
@Import(OrderService.class)
class OrderServiceTest {
}

// WRONG: Using @JsonTest for controller routing, validation, or security behavior.
@JsonTest
class OrderControllerTest {
}

// CORRECT: Use @WebMvcTest with MockMvc for controller-layer HTTP behavior.
@WebMvcTest(OrderController.class)
class OrderControllerTest {
}
```

## Gotchas
- Test slices load only the beans needed for that slice; autowiring unrelated application beans will fail.
- `@DataJpaTest` transactions roll back by default, which keeps tests isolated without manual cleanup.
- `@WebMvcTest` validates controller mappings and MVC configuration but does not start a real HTTP server.
- `@JsonTest` focuses on JSON converters and serializers; it does not prove HTTP status codes or routing.
- `@SpringBootTest` is valuable for integration coverage but is slower and should be used sparingly.

## Related
- java/spring/boot-basics.md
- java/spring/spring-mvc.md
- java/spring/spring-boot-3-graalvm.md
