---
id: "swift-testing-swift-testing"
title: "Swift Testing Framework (Swift 6): @Test, @Suite, #expect"
language: "swift"
category: "testing"
tags: ["swift", "testing", "swift-testing", "suite", "expect"]
version: "6.0+"
retrieval_hint: "swift testing framework @Test @Suite #expect Swift 6"
last_verified: "2026-05-24"
confidence: "high"
---

# Swift Testing Framework (Swift 6): @Test, @Suite, #expect

## When to Use
- Writing tests in Swift 6+ projects
- Replacing XCTest with the modern Swift Testing framework
- Using parameterized tests
- Organizing tests with tags and suites

## Standard Pattern

```swift
import Testing

// --- Basic Suite and Test ---
struct UserServiceTests {

    // Simple test
    @Test("User creation sets correct name")
    func createUser() {
        let user = User(id: 1, name: "Alice")
        #expect(user.name == "Alice")
        #expect(user.id == 1)
    }

    // Throwing test
    @Test("Fetch user returns expected data")
    func fetchUser() async throws {
        let service = MockUserService()
        service.mockResult = .success(User(id: 1, name: "Bob"))

        let user = try await service.fetchUser(id: 1)
        #expect(user.name == "Bob")
    }
}

// --- Parameterized Tests ---
struct ValidationTests {

    @Test("Email validation", arguments: [
        "alice@example.com",
        "bob@test.co.uk",
        "user+tag@domain.com",
    ])
    func validEmail(_ email: String) {
        #expect(email.isValidEmail)
    }

    @Test("Invalid emails rejected", arguments: [
        "not-an-email",
        "@domain.com",
        "user@",
    ])
    func invalidEmail(_ email: String) {
        #expect(!email.isValidEmail)
    }
}

// --- Tagged Tests ---
extension Tag {
    @Tag static var critical: Self
    @Tag static var networking: Self
    @Tag static var database: Self
}

struct OrderServiceTests {

    @Test(.tags(.critical))
    func placeOrder() async throws {
        let order = try await placeOrder(items: ["book"])
        #expect(order.status == .confirmed)
    }

    @Test(.tags(.networking))
    func orderNetworkCall() async throws {
        let response = try await sendOrderRequest()
        #expect(response.statusCode == 201)
    }
}

// --- Suite Hierarchy ---
@Suite("User Domain Tests")
struct UserDomainTests {

    @Suite("Creation")
    struct CreationTests {
        @Test
        func defaultValues() { /* ... */ }

        @Test
        func withCustomValues() { /* ... */ }
    }

    @Suite("Validation")
    struct ValidationTests {
        @Test
        func validInput() { /* ... */ }
    }
}

// --- Bug Reproduction (known issue) ---
struct RegressionTests {

    @Test("Bug #42: Empty name crashes display",
          .bug("https://github.com/org/repo/issues/42"))
    func emptyName() {
        let user = User(id: 1, name: "")
        let display = user.displayName  // Should not crash
        #expect(display == "Unknown")
    }
}

// --- Conditions and Timeouts ---
struct ConditionalTests {

    @Test("iOS 17+ feature availability")
    func iOSFeature() throws {
        try Testing.skipIf(!isIOS17orLater(), "Requires iOS 17+")
        let result = callIOS17API()
        #expect(result != nil)
    }

    @Test(.timeLimit(.minutes(1)))
    func slowOperation() async {
        let result = await performSlowCalculation()
        #expect(result.isValid)
    }
}
```

## Common Mistakes

```swift
// WRONG: Mixing XCTest assertions with Swift Testing import
import XCTest

@Test
func myTest() {
    XCTAssertEqual(a, b)  // Works but mixes frameworks
}

// CORRECT: Use Swift Testing macros exclusively
import Testing

@Test
func myTest() {
    #expect(a == b)
}


// WRONG: Mutable state across tests in the same suite
struct UserTests {
    var user = User(id: 1, name: "Alice")  // Shared mutable state!

    @Test
    func testName() {
        user.name = "Bob"  // Affects other tests!
        #expect(user.name == "Bob")
    }

    @Test
    func testId() {
        #expect(user.id == 1)  // May fail if testName ran first
    }
}

// CORRECT: Each test is independent
struct UserTests {
    @Test
    func testName() {
        let user = User(id: 1, name: "Alice")
        #expect(user.name == "Alice")
    }

    @Test
    func testId() {
        let user = User(id: 1, name: "Alice")
        #expect(user.id == 1)
    }
}


// WRONG: Wrong import — missing Swift Testing
import XCTest  // Using XCTest instead

@Test
func myTest() {
    #expect(true)  // Compiler error: can't find #expect
}

// CORRECT: Import Testing
import Testing

@Test
func myTest() {
    #expect(true)
}
```

## Gotchas
- **Availability**: Swift Testing requires Swift 6.0+ and Xcode 16+. It is not available on older toolchains. Check your deployment target and tools version.
- **XCTest coexistence**: You can use both frameworks in the same target. XCTest and Swift Testing tests run side by side. XCTest tests are discovered at runtime; Swift Testing tests are discovered at compile time.
- **#expect vs #require**: `#expect` records a failure but continues. `#require` stops the test immediately if the condition fails (like `guard`). Use `#require` for optionals that following code depends on.
- **Test order**: Like XCTest, Swift Testing does not guarantee test execution order within a suite. Each test should be fully independent.
- **Suite as struct**: Suites are typically `struct` types (not `class`). They are re-initialized for each test, so stored properties are fresh per test.
- **`withKnownIssue`**: Use `withKnownIssue` for known bugs or flaky tests that you want to track without failing the build.
- **Tags for filtering**: Tags let you run subsets: `--filter "critical"`. Tag test methods with `.tags(.critical, .networking)`.

## Related
- swift/testing/basics.md
- swift/stdlib/concurrency.md
