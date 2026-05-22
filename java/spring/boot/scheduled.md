---
id: "java-spring-boot-scheduled"
title: "Spring Boot Scheduled Tasks"
language: "java"
category: "web"
subcategory: "scheduling"
tags: ["spring", "boot", "scheduled", "cron", "fixed-rate", "async", "task"]
version: "17+"
retrieval_hint: "Spring Boot Scheduled cron fixedRate fixedDelay async task scheduling"
last_verified: "2026-05-22"
confidence: "high"
---

# Spring Boot Scheduled Tasks

## When to Use
- Periodic cleanup jobs (expired sessions, temp files)
- Data synchronization with external systems
- Report generation (daily/weekly/monthly)
- Polling for new data from message queues or APIs

## Standard Pattern

```java
// --- Enable scheduling ---
@SpringBootApplication
@EnableScheduling
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}

// --- Scheduled tasks ---
@Component
public class ScheduledTasks {
    private static final Logger log = LoggerFactory.getLogger(ScheduledTasks.class);

    private final CleanupService cleanupService;
    private final SyncService syncService;

    public ScheduledTasks(CleanupService cleanupService, SyncService syncService) {
        this.cleanupService = cleanupService;
        this.syncService = syncService;
    }

    // Fixed rate: runs every 60 seconds (regardless of previous execution time)
    @Scheduled(fixedRate = 60_000)
    public void syncData() {
        log.info("Starting data sync");
        syncService.syncLatestData();
    }

    // Fixed delay: runs 30 seconds AFTER previous execution completes
    @Scheduled(fixedDelay = 30_000)
    public void processQueue() {
        log.info("Processing pending items");
        cleanupService.processPendingItems();
    }

    // Cron: every day at 2 AM
    @Scheduled(cron = "0 0 2 * * *")
    public void dailyCleanup() {
        log.info("Running daily cleanup");
        cleanupService.deleteExpiredSessions();
        cleanupService.archiveOldRecords();
    }

    // Cron with timezone
    @Scheduled(cron = "0 0 9 * * MON-FRI", zone = "America/New_York")
    public void weekdayReport() {
        log.info("Generating daily report");
    }

    // Initial delay + fixed rate
    @Scheduled(initialDelay = 10_000, fixedRate = 300_000)
    public void withInitialDelay() {
        // First run after 10s, then every 5 minutes
    }
}

// --- Async scheduling (non-blocking) ---
@Configuration
@EnableAsync
public class AsyncConfig {
    @Bean
    public TaskScheduler taskScheduler() {
        ThreadPoolTaskScheduler scheduler = new ThreadPoolTaskScheduler();
        scheduler.setPoolSize(5);
        scheduler.setThreadNamePrefix("scheduled-");
        return scheduler;
    }
}
```

## Common Mistakes

```java
// WRONG: Long-running task blocks the scheduler
@Scheduled(fixedRate = 60_000)
public void longRunningTask() {
    // Takes 2 minutes — scheduler thread is blocked, next execution delayed
    processAllRecords();
}

// CORRECT: Use @Async for long-running scheduled tasks
@Async
@Scheduled(fixedRate = 60_000)
public void longRunningTask() {
    processAllRecords();  // Runs in separate thread pool
}

// WRONG: Not handling exceptions (scheduler stops!)
@Scheduled(fixedRate = 60_000)
public void riskyTask() {
    externalApiCall();  // If this throws, scheduler may stop
}

// CORRECT: Catch exceptions to keep scheduler alive
@Scheduled(fixedRate = 60_000)
public void riskyTask() {
    try {
        externalApiCall();
    } catch (Exception e) {
        log.error("Scheduled task failed", e);
    }
}

// WRONG: Using fixedRate for unpredictable tasks
@Scheduled(fixedRate = 5000)
public void processItems() {
    // Sometimes takes 1s, sometimes takes 30s
    // fixedRate doesn't wait for completion
}

// CORRECT: Use fixedDelay for sequential execution
@Scheduled(fixedDelay = 5000)
public void processItems() {
    // Waits 5s AFTER this completes before running again
}
```

## Gotchas
- `@Scheduled` uses a single-threaded scheduler by default — multiple tasks block each other
- Configure `TaskScheduler` with a thread pool for parallel scheduled tasks
- `fixedRate` fires at fixed intervals (may overlap); `fixedDelay` waits for completion
- Cron expressions have 6 fields (seconds first), not 5 like Unix cron
- `@Scheduled` methods must be void and take no parameters
- Exceptions in `@Scheduled` methods can kill the scheduler thread — always catch them
- Use `@EnableScheduling` to activate; without it, `@Scheduled` is silently ignored
- `zone` parameter in `@Scheduled(cron=..., zone="UTC")` for timezone-aware cron

## Related
- java/spring/boot-basics.md
- java/spring/boot/actuator.md
- java/spring/boot/caching.md
