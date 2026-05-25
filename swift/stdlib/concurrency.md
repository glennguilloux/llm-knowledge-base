---
id: "swift-stdlib-concurrency"
title: "Swift Concurrency: async/await, Task, Actor, and Sendable"
language: "swift"
category: "stdlib"
tags: ["swift", "concurrency", "async-await", "Task", "TaskGroup", "actor", "Sendable", "MainActor"]
version: "5.9+"
retrieval_hint: "swift async await Task TaskGroup actor Sendable MainActor structured concurrency"
last_verified: "2026-05-24"
confidence: "high"
---

# Swift Concurrency: async/await, Task, Actor, and Sendable

## When to Use
- Performing asynchronous operations with async/await
- Running concurrent tasks with Task and TaskGroup
- Protecting shared mutable state with actors
- Ensuring thread safety with Sendable
- Updating UI from background threads with MainActor

## Standard Pattern

```swift
// async/await — the foundation of Swift concurrency
func fetchUser(id: Int) async throws -> User {
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(User.self, from: data)
}

// Using async/await
Task {
    do {
        let user = try await fetchUser(id: 1)
        print("User: \(user.name)")
    } catch {
        print("Error: \(error)")
    }
}

// Task — represents a unit of asynchronous work
func loadData() async {
    // Fire-and-forget task
    Task {
        let data = try? await fetchData()
        print("Data loaded: \(data)")
    }
    
    // Task with return value
    let task = Task {
        return try await fetchUser(id: 1)
    }
    
    // Await the result
    let user = try? await task.value
}

// TaskGroup — run multiple tasks concurrently
func fetchAllUsers(ids: [Int]) async -> [User] {
    await withTaskGroup(of: User?.self) { group in
        for id in ids {
            group.addTask {
                try? await fetchUser(id: id)
            }
        }
        
        var users: [User] = []
        for await user in group {
            if let user = user {
                users.append(user)
            }
        }
        return users
    }
}

// Structured concurrency — async let
func loadDashboard() async throws -> Dashboard {
    async let user = fetchUser(id: 1)
    async let orders = fetchOrders(userId: 1)
    async let notifications = fetchNotifications(userId: 1)
    
    // All three run concurrently
    return try await Dashboard(
        user: user,
        orders: orders,
        notifications: notifications
    )
}

// Actor — protects shared mutable state
actor Counter {
    private var value = 0
    
    func increment() {
        value += 1
    }
    
    func getValue() -> Int {
        return value
    }
}

// Using actor
let counter = Counter()
Task {
    await counter.increment()
    let value = await counter.getValue()
    print("Counter: \(value)")
}

// MainActor — ensures code runs on the main thread
@MainActor
class UserViewModel: ObservableObject {
    @Published var users: [User] = []
    @Published var isLoading = false
    
    func loadUsers() async {
        isLoading = true
        do {
            users = try await userService.fetchAll()
        } catch {
            // Handle error
        }
        isLoading = false
    }
}

// Sendable — types that can be safely shared across concurrency domains
struct User: Sendable {
    let id: Int
    let name: String
    let email: String
}

// @Sendable closure — captures must be safe to share
func processInBackground(_ work: @Sendable @escaping () -> Void) {
    DispatchQueue.global().async {
        work()
    }
}

// AsyncSequence — iterate over async values
func observeNotifications() async {
    let stream = NotificationCenter.default.notifications(named: .newMessage)
    for await notification in stream {
        handleNotification(notification)
    }
}

// Task cancellation
func longRunningTask() async throws {
    for i in 0..<1000 {
        try Task.checkCancellation()  // Throws CancellationException if cancelled
        await processItem(i)
    }
}

// Using withTaskCancellationHandler
func fetchWithCancellation() async throws -> Data {
    try await withTaskCancellationHandler {
        try await URLSession.shared.data(from: url).0
    } onCancel: {
        // Cleanup when task is cancelled
        print("Task cancelled")
    }
}
```

## Common Mistakes

```swift
// WRONG: Calling async function without await
func loadUser() {
    let user = fetchUser(id: 1)  // Compile error: async call in non-async context
}

// CORRECT: Use await in async context or Task
func loadUser() async {
    let user = try await fetchUser(id: 1)
}
// Or:
Task {
    let user = try await fetchUser(id: 1)
}

// WRONG: Not handling task cancellation
func longRunning() async {
    for i in 0..<1000000 {
        process(i)  // Won't respond to cancellation!
    }
}

// CORRECT: Check for cancellation
func longRunning() async throws {
    for i in 0..<1000000 {
        try Task.checkCancellation()
        process(i)
    }
}

// WRONG: Accessing shared mutable state without actor
class Counter {
    var value = 0
    func increment() { value += 1 }  // Data race!
}

// CORRECT: Use actor for shared mutable state
actor Counter {
    private var value = 0
    func increment() { value += 1 }
}

// WRONG: Not using MainActor for UI updates
class ViewModel: ObservableObject {
    @Published var name = ""
    
    func load() async {
        let user = try await fetchUser(id: 1)
        name = user.name  // May not be on main thread!
    }
}

// CORRECT: Use @MainActor for UI-related classes
@MainActor
class ViewModel: ObservableObject {
    @Published var name = ""
    
    func load() async {
        let user = try await fetchUser(id: 1)
        name = user.name  // Guaranteed to be on main thread
    }
}

// WRONG: Forgetting that async let is scoped
func badExample() {
    async let user = fetchUser(id: 1)  // user is only available in this scope
}
// user is not accessible here!

// CORRECT: Await async let within the same scope
func goodExample() async {
    async let user = fetchUser(id: 1)
    async let orders = fetchOrders()
    let result = await (try user, try orders)
}
```

## Gotchas
- `async` functions run in the Swift concurrency system, NOT on a specific thread. The system decides.
- `await` suspends the current task but does NOT block the thread. Other tasks can run.
- `Task { }` creates an unstructured task. It inherits the actor context and priority of the caller.
- `Task.detached { }` creates a task that doesn't inherit context (priority, actor).
- Actors protect their state — you MUST use `await` to access actor-isolated properties/methods.
- `@MainActor` ensures code runs on the main thread. Use it for UI-related classes.
- `Sendable` types can be safely shared across concurrency domains. Value types are implicitly Sendable.
- `Task.checkCancellation()` throws if the task was cancelled. Use it in long-running loops.
- `async let` creates a child task. All `async let` bindings must be awaited before the scope ends.
- `withTaskGroup` runs child tasks concurrently and waits for all to complete.
- Structured concurrency: child tasks are cancelled when the parent is cancelled.

## Related
- swift/stdlib/basics.md
- swift/stdlib/closures.md
- swift/stdlib/error-handling.md
- swift/stdlib/protocols-generics.md
