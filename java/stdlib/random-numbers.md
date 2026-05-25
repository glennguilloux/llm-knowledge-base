---
id: "java-stdlib-random-numbers"
title: "Java Random Number Generation"
language: "java"
category: "stdlib"
subcategory: "utilities"
tags: ["random", "threadlocalrandom", "securerandom", "math-random", "random-range"]
version: "17+"
retrieval_hint: "Java random numbers ThreadLocalRandom SecureRandom random int range random from list"
last_verified: "2026-05-24"
confidence: "high"
---

# Java Random Number Generation

## When to Use
- Generating random numbers in multi-threaded code (ThreadLocalRandom)
- Security-sensitive random values: tokens, passwords, session IDs (SecureRandom)
- Random selection from lists, arrays, or ranges
- Games, simulations, and probabilistic algorithms

## Standard Pattern

```java
import java.security.SecureRandom;
import java.util.List;
import java.util.Random;
import java.util.concurrent.ThreadLocalRandom;
import java.util.stream.IntStream;

public class RandomExamples {

    // ThreadLocalRandom for most use cases (no contention in multi-threaded code)
    public static int randomInt(int origin, int bound) {
        return ThreadLocalRandom.current().nextInt(origin, bound);
    }

    public static long randomLong(long origin, long bound) {
        return ThreadLocalRandom.current().nextLong(origin, bound);
    }

    public static double randomDouble(double origin, double bound) {
        return ThreadLocalRandom.current().nextDouble(origin, bound);
    }

    // SecureRandom for security-sensitive operations
    public static String generateToken(int byteLength) {
        byte[] bytes = new byte[byteLength];
        SecureRandom secureRandom = new SecureRandom();
        secureRandom.nextBytes(bytes);
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }

    public static int secureRandomInt(int origin, int bound) {
        SecureRandom secureRandom = new SecureRandom();
        return secureRandom.nextInt(bound - origin) + origin;
    }

    // Random element from a list
    public static <T> T randomElement(List<T> list) {
        if (list == null || list.isEmpty()) {
            throw new IllegalArgumentException("List must not be null or empty");
        }
        int index = ThreadLocalRandom.current().nextInt(list.size());
        return list.get(index);
    }

    // Shuffle a list (Fisher-Yates)
    public static <T> void shuffleList(List<T> list) {
        java.util.Collections.shuffle(list, ThreadLocalRandom.current());
    }

    // Generate stream of random ints in range
    public static IntStream randomIntStream(int count, int origin, int bound) {
        return ThreadLocalRandom.current().ints(count, origin, bound);
    }

    public static void main(String[] args) {
        System.out.println("Random int [1, 100): " + randomInt(1, 100));
        System.out.println("Random double [0.0, 1.0): " + randomDouble(0.0, 1.0));
        System.out.println("Secure token: " + generateToken(16));
        System.out.println("Random from list: " + randomElement(List.of("apple", "banana", "cherry")));

        List<String> items = new java.util.ArrayList<>(List.of("a", "b", "c", "d", "e"));
        shuffleList(items);
        System.out.println("Shuffled: " + items);

        System.out.print("5 random ints [1,10): ");
        randomIntStream(5, 1, 10).forEach(n -> System.out.print(n + " "));
        System.out.println();
    }
}
```

## Common Mistakes

```java
// WRONG: Creating new Random instance in a tight loop or method
public int rollDice() {
    Random rand = new Random();           // New instance every call!
    return rand.nextInt(6) + 1;           // Can produce poor randomness if called rapidly
}

// CORRECT: Use ThreadLocalRandom, or reuse a single Random instance
public int rollDice() {
    return ThreadLocalRandom.current().nextInt(1, 7);  // Bound is exclusive
}

// WRONG: Using Math.random() - slow, imprecise range control, not uniform for ints
int value = (int) (Math.random() * 100);  // [0, 100) but floating-point imprecision

// CORRECT: Use ThreadLocalRandom for full range control
int value = ThreadLocalRandom.current().nextInt(100);  // [0, 100), always uniform

// WRONG: Reusing Random instance across threads - contention and correlated output
private static final Random SHARED = new Random();  // Thread-safe but contended

// CORRECT: Use ThreadLocalRandom for thread-local generation without contention
int value = ThreadLocalRandom.current().nextInt();

// WRONG: nextInt(bound) where bound is 0 - throws IllegalArgumentException
int value = ThreadLocalRandom.current().nextInt(0);  // IAE!

// CORRECT: Guard against zero or negative bounds
public static int safeNextInt(int origin, int bound) {
    if (origin >= bound) throw new IllegalArgumentException("origin must be < bound");
    return ThreadLocalRandom.current().nextInt(origin, bound);
}

// WRONG: Assuming Math.random() includes 1.0 - it never does, and casting truncates
int value = (int) (Math.random() * 10);  // Can never produce 9.999..., max is 9

// CORRECT: ThreadLocalRandom with exclusive upper bound (clearer semantics)
int value = ThreadLocalRandom.current().nextInt(10);  // [0, 10) = 0..9
```

## Gotchas
- `ThreadLocalRandom.current().nextInt(origin, bound)` - the `bound` is **exclusive**, just like `Random.nextInt(bound)` returns `[0, bound)`
- `Math.random()` returns `[0.0, 1.0)` - never exactly 1.0, so `(int)(Math.random() * N)` gives `[0, N-1]` but with floating-point non-uniformity for large N
- `SecureRandom` is significantly slower than `ThreadLocalRandom` - use it only when unpredictability matters (tokens, cryptography)
- Creating a new `Random()` instance with no seed uses `System.nanoTime()`; if two instances are created in quick succession, they may generate identical sequences
- `Collections.shuffle(List, Random)` with a fixed-seed `Random` produces the same shuffle every time - useful for testing, dangerous in production
- `ThreadLocalRandom` cannot be seeded - if you need reproducible random sequences (e.g., testing), use `new Random(seed)` explicitly

## Related
- java/stdlib/collections.md
- java/stdlib/file-io.md
