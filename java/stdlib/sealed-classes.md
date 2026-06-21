---
id: "java-stdlib-sealed-classes"
title: "Sealed Classes and Interfaces in Java (17+)"
language: "java"
category: "stdlib"
subcategory: "type-system"
tags: ["java", "sealed-classes", "sealed-interfaces", "pattern-matching", "jdk17", "jdk21", "permits"]
version: "17+"
retrieval_hint: "Java sealed class interface permits pattern matching exhaustive switch records"
last_verified: "2026-05-25"
confidence: "high"
---

# Sealed Classes and Interfaces in Java (17+)

## When to Use
- Modeling a fixed set of subtypes (e.g., AST nodes, API responses, payment methods)
- Enforcing exhaustive pattern matching (the compiler checks you handled all cases)
- Replacing enum-like class hierarchies where you need per-type state or behavior
- Building type-safe domain models where the set of variants is known and bounded

## Standard Pattern

```java
// --- Basic sealed class hierarchy ---
// The sealed class defines the permitted subtypes
public sealed class Payment permits CreditCard, PayPal, Crypto {
    private final double amount;

    public Payment(double amount) {
        this.amount = amount;
    }

    public double getAmount() { return amount; }
}

// Permitted subclass 1: final (cannot be extended further)
public final class CreditCard extends Payment {
    private final String cardNumber;
    private final String cvv;

    public CreditCard(double amount, String cardNumber, String cvv) {
        super(amount);
        this.cardNumber = cardNumber;
        this.cvv = cvv;
    }

    public String getCardNumber() { return cardNumber; }
    public String getLastFour() { return cardNumber.substring(cardNumber.length() - 4); }
}

// Permitted subclass 2: final
public final class PayPal extends Payment {
    private final String email;

    public PayPal(double amount, String email) {
        super(amount);
        this.email = email;
    }

    public String getEmail() { return email; }
}

// Permitted subclass 3: sealed (limited further extension)
public sealed class Crypto extends Payment permits Bitcoin, Ethereum {
    public Crypto(double amount) { super(amount); }
}

public final class Bitcoin extends Crypto {
    private final String walletAddress;
    public Bitcoin(double amount, String walletAddress) {
        super(amount);
        this.walletAddress = walletAddress;
    }
}

public final class Ethereum extends Crypto {
    private final String contractAddress;
    public Ethereum(double amount, String contractAddress) {
        super(amount);
        this.contractAddress = contractAddress;
    }
}

// --- Exhaustive pattern matching with switch (JDK 21+) ---
public String processPayment(Payment payment) {
    return switch (payment) {
        case CreditCard c -> "Processing credit card ending in " + c.getLastFour();
        case PayPal p -> "Processing PayPal for " + p.getEmail();
        case Bitcoin b -> "Processing Bitcoin to " + b.getWalletAddress();
        case Ethereum e -> "Processing Ethereum contract " + e.getContractAddress();
        // No default needed! The compiler verifies all cases are covered.
        // If you add a new Payment subtype, this switch won't compile until handled.
    };
}

// --- Sealed interface with records (cleanest pattern) ---
public sealed interface ApiResponse permits Success, Error, Loading {}

public record Success<T>(T data, String message) implements ApiResponse {}
public record Error(int code, String message) implements ApiResponse {}
public record Loading(String status) implements ApiResponse {}

// --- Usage with exhaustive switch ---
public <T> String render(ApiResponse response) {
    return switch (response) {
        case Success<T> s -> "✅ " + s.message() + ": " + s.data();
        case Error e -> "❌ Error " + e.code() + ": " + e.message();
        case Loading l -> "⏳ " + l.status();
    };
}

// --- Sealed class with records (JDK 16+ syntax) ---
public sealed interface Vehicle permits Car, Truck, Motorcycle {}

// Records can implement sealed interfaces
public record Car(String make, String model, int doors) implements Vehicle {}
public record Truck(String make, int payloadKg) implements Vehicle {}
public record Motorcycle(String make, boolean hasSidecar) implements Vehicle {}

public String describeVehicle(Vehicle v) {
    return switch (v) {
        case Car c -> "Car: " + c.make() + " " + c.model() + " (" + c.doors() + " doors)";
        case Truck t -> "Truck: " + t.make() + ", payload " + t.payloadKg() + "kg";
        case Motorcycle m -> "Motorcycle: " + m.make() + (m.hasSidecar() ? " with sidecar" : "");
    };
}
```

## Common Mistakes

```java
// WRONG: Permitted subclass in a different module without open module
// Sealed class in module A:
package com.app.payments;
public sealed class Payment permits CreditCard { ... }
public final class CreditCard extends Payment { ... }

// Subclass in module B:
package com.app.extras;
public final class Bitcoin extends Payment { ... }
// ERROR: Bitcoin is not in the permits clause!
// Sealed hierarchies must be in the SAME module (or the same compilation unit)

// WRONG: Permitted subclass is neither final, sealed, nor non-sealed
public sealed class Shape permits Circle, Square { ... }

public class Circle extends Shape { ... }
// ERROR: Circle must be final, sealed, or non-sealed!

// CORRECT: Mark explicitly
public final class Circle extends Shape { ... }          // No further extension
public sealed class Square extends Shape permits ... {}  // Limited extension
public non-sealed class Triangle extends Shape { ... }   // Open for extension

// WRONG: Using switch without covering all sealed subtypes
String handlePayment(Payment p) {
    return switch (p) {
        case CreditCard c -> "card";
        // Missing PayPal, Crypto subtypes — won't compile!
    };
}

// CORRECT: Either cover all subtypes or add a default branch
String handlePayment(Payment p) {
    return switch (p) {
        case CreditCard c -> "card";
        case PayPal pp -> "paypal";
        case Bitcoin b -> "bitcoin";
        case Ethereum e -> "ethereum";
        // No default needed — exhaustive
    };
}

// WRONG: Using instanceof cascades instead of sealed pattern matching
// Before sealed classes, you'd write ugly instanceof chains:
if (vehicle instanceof Car c) {
    return c.make();
} else if (vehicle instanceof Truck t) {
    return t.make();
} else {
    throw new IllegalArgumentException("Unknown type");
}

// CORRECT: Use switch with pattern matching on sealed types
// Compiler checks exhaustiveness — no else branch needed.
return switch (vehicle) {
    case Car c -> c.make();
    case Truck t -> t.make();
    case Motorcycle m -> m.make();
};
```

## Gotchas
- **`permits` clause order doesn't matter but all permitted types must be listed:** Every direct subclass must be declared in the `permits` clause. Missing one is a compile error. The subtypes can be in any order.
- **Records + sealed interfaces = best combo:** Records provide the data carrier, sealed interfaces provide the type constraint, and pattern matching provides the dispatch. Together they replace the visitor pattern for most cases.
- **Non-sealed breaks exhaustive checking:** A `non-sealed` subclass means the hierarchy is OPEN. The compiler can't check exhaustiveness because anyone can extend a `non-sealed` class. Use `non-sealed` sparingly — it defeats the purpose of sealing.
- **Sealed classes + pattern matching requires JDK 21 for full power:** JDK 17 supports sealed classes but pattern matching for switch is preview. JDK 21 finalizes pattern matching for switch (JEP 441), including exhaustive sealed switches with `null` support.
- **Serialization with sealed classes:** If you serialize sealed class instances, deserialization creates instances of the permitted subtypes. The JVM validates the type at deserialization time, so you can't inject invalid subtypes. This is a security benefit over non-sealed hierarchies.

## Related
- java/stdlib/records.md
- java/stdlib/optional.md
