---
id: "java-concurrency-locks-reentrant"
title: "Java Reentrant Locks"
language: "java"
category: "concurrency"
subcategory: "locks"
tags: ["java", "concurrency", "ReentrantLock", "tryLock", "Condition", "fair-lock", "deadlock", "lock-ordering"]
version: "17+"
retrieval_hint: "Java ReentrantLock tryLock Condition fair lock lock ordering deadlock prevention interruptible locking"
last_verified: "2026-06-20"
confidence: "medium"
---

# Java Reentrant Locks

## When to Use
- Need interruptible locking, timed acquisition, or explicit try-fail behavior
- Protecting shared mutable state when `synchronized` is too coarse or not expressive enough
- Coordinating threads with `Condition` objects such as wait/signal queues
- Preventing deadlocks with a consistent lock acquisition order
- Supporting fairness policies for contention-sensitive resources

## Standard Pattern

```java
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

public class ReentrantLockPatterns {

    private final ReentrantLock lock = new ReentrantLock(true);
    private final Condition fundsAvailable = lock.newCondition();
    private final Map<String, BigDecimal> balances = new HashMap<>();

    public ReentrantLockPatterns(Map<String, BigDecimal> initialBalances) {
        balances.putAll(initialBalances);
    }

    public void transfer(String fromAccountId, String toAccountId, BigDecimal amount)
            throws InterruptedException {
        List<String> accountIds = List.of(fromAccountId, toAccountId).stream()
            .distinct()
            .sorted(Comparator.naturalOrder())
            .toList();
        List<String> acquired = new ArrayList<>(accountIds.size());

        try {
            for (String accountId : accountIds) {
                if (!lock.tryLock(2, TimeUnit.SECONDS)) {
                    throw new IllegalStateException("Timed out waiting for " + accountId);
                }
                acquired.add(accountId);
            }

            balances.compute(fromAccountId, (id, balance) -> balance.subtract(amount));
            balances.compute(toAccountId, (id, balance) -> balance.add(amount));
        } finally {
            for (int i = acquired.size() - 1; i >= 0; i--) {
                lock.unlock();
            }
        }
    }

    public void awaitFundsAvailable() throws InterruptedException {
        lock.lock();
        try {
            while (!hasFundsAvailable()) {
                fundsAvailable.await();
            }
        } finally {
            lock.unlock();
        }
    }

    public void signalFundsAvailable() {
        lock.lock();
        try {
            fundsAvailable.signalAll();
        } finally {
            lock.unlock();
        }
    }

    private boolean hasFundsAvailable() {
        return balances.values().stream().anyMatch(balance -> balance.signum() > 0);
    }
}
```

## Common Mistakes

```java
// WRONG: Forgetting to unlock in a finally block
lock.lock();
doWork();
lock.unlock();

// CORRECT: Always unlock in finally
lock.lock();
try {
    doWork();
} finally {
    lock.unlock();
}

// WRONG: Ignoring tryLock failure
if (lock.tryLock()) {
    doWork();
}
// Work is silently skipped when the lock is busy.

// CORRECT: Handle timed acquisition failure explicitly
if (!lock.tryLock(100, TimeUnit.MILLISECONDS)) {
    throw new IllegalStateException("Resource busy");
}

// WRONG: Acquiring multiple locks in caller-dependent order
lock(accountA, accountB);
lock(accountB, accountA);

// CORRECT: Sort lock identities and always acquire in the same order
List<String> ids = List.of(from, to).stream().sorted().toList();

// WRONG: Using Condition with if instead of while
if (!ready) {
    condition.await();
}

// CORRECT: Re-check the predicate after every wakeup
while (!ready) {
    condition.await();
}
```

## Gotchas
- `ReentrantLock` must be unlocked explicitly; missing `unlock` corrupts availability.
- Fair locks reduce throughput and should be used only when starvation is a real concern.
- `Condition.await` must be called in a loop because spurious wakeups are allowed.
- Timed `tryLock` throws `InterruptedException` and must be handled like other interruptible operations.
- Consistent lock ordering prevents deadlocks when multiple locks protect related state.

## Related
- java/concurrency/virtual-threads-deep.md
- java/patterns/double-checked-locking.md
- java/patterns/guarded-suspension.md