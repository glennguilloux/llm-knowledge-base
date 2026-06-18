---
id: "swift-testing-basics"
title: "Swift Testing with XCTest: Async Testing and Mock Patterns"
language: "swift"
category: "testing"
tags: ["swift", "testing", "xctest", "async", "mocking"]
version: "5.9+"
retrieval_hint: "swift XCTest async testing mock patterns unit testing"
last_verified: "2026-05-24"
confidence: "high"
---

# Swift Testing with XCTest: Async Testing and Mock Patterns

## When to Use
- Writing unit tests for Swift code
- Testing async functions with XCTest
- Mocking dependencies with protocols
- Setting up test fixtures

## Standard Pattern

```swift
import XCTest

// --- Protocol for Mocking ---
protocol UserServiceProtocol {
    func fetchUser(id: Int) async throws -> User
    func saveUser(_ user: User) async throws
}

// --- Mock Implementation ---
final class MockUserService: UserServiceProtocol {
    var fetchUserResult: Result<User, Error>?
    var savedUsers: [User] = []
    var fetchCallCount = 0

    func fetchUser(id: Int) async throws -> User {
        fetchCallCount += 1
        guard let result = fetchUserResult else {
            throw MockError.unexpectedCall
        }
        return try result.get()
    }

    func saveUser(_ user: User) async throws {
        savedUsers.append(user)
    }
}

enum MockError: Error {
    case unexpectedCall
    case simulatedFailure
}

// --- Production Code ---
struct User: Equatable {
    let id: Int
    let name: String
}

final class UserViewModel {
    let service: UserServiceProtocol

    init(service: UserServiceProtocol) {
        self.service = service
    }

    func loadUser(id: Int) async throws -> String {
        let user = try await service.fetchUser(id: id)
        return "User: \(user.name)"
    }
}

// --- Test Class ---
final class UserViewModelTests: XCTestCase {
    var mockService: MockUserService!
    var viewModel: UserViewModel!

    override func setUp() async throws {
        try await super.setUp()
        mockService = MockUserService()
        viewModel = UserViewModel(service: mockService)
    }

    override func tearDown() async throws {
        mockService = nil
        viewModel = nil
        try await super.tearDown()
    }

    // --- Basic Async Test ---
    func testLoadUserSuccess() async throws {
        // Given
        let expectedUser = User(id: 1, name: "Alice")
        mockService.fetchUserResult = .success(expectedUser)

        // When
        let result = try await viewModel.loadUser(id: 1)

        // Then
        XCTAssertEqual(result, "User: Alice")
        XCTAssertEqual(mockService.fetchCallCount, 1)
    }

    // --- Failure Test ---
    func testLoadUserFailure() async {
        // Given
        mockService.fetchUserResult = .failure(MockError.simulatedFailure)

        // When & Then
        do {
            _ = try await viewModel.loadUser(id: 1)
            XCTFail("Expected error to be thrown")
        } catch MockError.simulatedFailure {
            // Expected — test passes
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }

    // --- Expectation Pattern (for callback-based code) ---
    func testAsyncCallback() {
        let expectation = expectation(description: "Callback invoked")

        performAsyncWork { result in
            XCTAssertEqual(result, "done")
            expectation.fulfill()
        }

        wait(for: [expectation], timeout: 2.0)
    }

    private func performAsyncWork(completion: @escaping (String) -> Void) {
        DispatchQueue.global().asyncAfter(deadline: .now() + 0.1) {
            completion("done")
        }
    }

    // --- Performance Test ---
    func testLoadUserPerformance() throws {
        mockService.fetchUserResult = .success(User(id: 1, name: "Alice"))

        measure {
            let semaphore = DispatchSemaphore(value: 0)
            Task {
                _ = try await viewModel.loadUser(id: 1)
                semaphore.signal()
            }
            semaphore.wait()
        }
    }
}
```

## Common Mistakes

```swift
// WRONG: Shared mutable state between tests (singleton)
class UserManager {
    static let shared = UserManager()
    var currentUser: User?
}

func testLogin() {
    UserManager.shared.currentUser = User(id: 1, name: "Alice")
    // Other tests are affected by this state!
}

// CORRECT: Fresh instance per test
func testLogin() {
    let manager = UserManager()
    manager.currentUser = User(id: 1, name: "Alice")
    // Each test gets a clean instance
}


// WRONG: Not marking test as async for async code
func testAsyncFunction() {
    let result = try await fetchData()  // ❌ Must be in async context
}

// CORRECT: Use async test method
func testAsyncFunction() async throws {
    let result = try await fetchData()
    XCTAssertEqual(result, "expected")
}


// WRONG: Using wait() on main thread (deadlocks)
func testWithExpectation() {
    let exp = expectation(description: "wait")
    DispatchQueue.main.async {
        exp.fulfill()
    }
    wait(for: [exp], timeout: 1.0)  // Deadlock on main queue!
}

// CORRECT: Use async test or background queue
func testWithExpectation() {
    let exp = expectation(description: "wait")
    DispatchQueue.global().async {
        exp.fulfill()
    }
    wait(for: [exp], timeout: 1.0)
}
```

## Gotchas
- **Test execution order**: XCTest does not guarantee test method execution order. Never depend on tests running in a specific sequence.
- **setUp/tearDown**: Use `setUp()` to create fresh state and `tearDown()` to clean up. Shared state between tests causes flaky failures.
- **Async test timeout**: Async tests using expectations have a default timeout. Always specify an explicit reasonable timeout. Tests failing due to timeout are flaky tests.
- **@MainActor tests**: Tests with `@MainActor` run on the main actor. UI-related tests should use this, but be aware of potential deadlocks with `wait()`.
- **XCTSkip**: Use `try XCTSkipIf(condition)` to conditionally skip tests (e.g., platform-specific features). This is better than commenting out tests.
- **NSManagedObject and threads**: Core Data objects are not thread-safe. Create a new context per test to avoid cross-test contamination.

## Related
- swift/testing/swift-testing.md
- swift/stdlib/networking.md
