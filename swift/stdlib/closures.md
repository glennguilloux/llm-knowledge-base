---
id: "swift-stdlib-closures"
title: "Swift Closures: Syntax, Trailing Closures, Capture Lists, and Memory"
language: "swift"
category: "stdlib"
tags: ["swift", "closures", "trailing-closures", "escaping", "capture-lists", "weak", "unowned"]
version: "5.9+"
retrieval_hint: "swift closure syntax trailing closures escaping capture lists weak unowned references higher-order functions"
last_verified: "2026-05-24"
confidence: "high"
---

# Swift Closures: Syntax, Trailing Closures, Capture Lists, and Memory

## When to Use
- Using closures for callbacks and completion handlers
- Writing trailing closure syntax for clean API design
- Handling memory management with capture lists (`weak`, `unowned`)
- Working with higher-order functions like `map`, `filter`, `sorted`

## Standard Pattern

```swift
// Basic closure syntax
let greet: (String) -> String = { name in
    return "Hello, \(name)!"
}
print(greet("Alice"))  // "Hello, Alice!"

// Shorthand argument names ($0, $1, $2)
let add: (Int, Int) -> Int = { $0 + $1 }
print(add(3, 5))  // 8

// Closure as function parameter
func execute(operation: () -> Void) {
    print("Before")
    operation()
    print("After")
}

// Trailing closure syntax (when closure is last argument)
execute {
    print("Executing!")
}

// Multiple trailing closures (Swift 5.3+)
func loadData(
    onSuccess: (Data) -> Void,
    onFailure: (Error) -> Void
) { /* ... */ }

loadData(
    onSuccess: { data in print("Got data: \(data)") },
    onFailure: { error in print("Error: \(error)") }
)

// Escaping closures — stored for later execution
var completionHandlers: [() -> Void] = []

func withCompletion(handler: @escaping () -> Void) {
    completionHandlers.append(handler)  // Stored — must be @escaping
}

// Non-escaping (default) — closure is called before function returns
func performImmediately(action: () -> Void) {
    action()  // Called immediately — no @escaping needed
}

// Capture lists — prevent retain cycles
class DataLoader {
    var data: String = ""
    
    func load() {
        // WRONG: Strong reference to self creates retain cycle
        // URLSession.shared.dataTask(with: url) { data, _, _ in
        //     self.data = String(data: data!, encoding: .utf8) ?? ""
        // }.resume()
        
        // CORRECT: Use [weak self] to prevent retain cycle
        URLSession.shared.dataTask(with: url) { [weak self] data, _, _ in
            guard let self = self else { return }
            self.data = String(data: data!, encoding: .utf8) ?? ""
        }.resume()
        
        // Or use [unowned self] when self will never be nil during closure lifetime
        URLSession.shared.dataTask(with: url) { [unowned self] data, _, _ in
            self.data = String(data: data!, encoding: .utf8) ?? ""
        }.resume()
    }
}

// Capture list with multiple captures
var counter = 0
let closure = { [weak self = someObject, counter] in
    // self is weak reference, counter is captured by value
}

// Autoclosure — wraps expression in closure automatically
func assert(_ condition: @autoclosure () -> Bool, _ message: String) {
    if !condition() {
        print("Assertion: \(message)")
    }
}
assert(2 + 2 == 4, "Math is broken")  // Expression auto-wrapped in closure

// Higher-order functions with closures
let numbers = [1, 2, 3, 4, 5]

// sorted with closure
let sorted = numbers.sorted { $0 > $1 }  // [5, 4, 3, 2, 1]

// filter with closure
let even = numbers.filter { $0 % 2 == 0 }  // [2, 4]

// map with closure
let doubled = numbers.map { $0 * 2 }  // [2, 4, 6, 8, 10]

// reduce with closure
let sum = numbers.reduce(0) { $0 + $1 }  // 15

// forEach with closure
numbers.forEach { print($0) }

// compactMap — map + remove nils
let strings = ["1", "2", "three", "4"]
let ints = strings.compactMap { Int($0) }  // [1, 2, 4]
```

## Common Mistakes

```swift
// WRONG: Creating a retain cycle with self in closure
class MyClass {
    var value = 0
    
    func setup() {
        // self strongly retains the closure, closure strongly retains self
        someAsyncWork {
            self.value = 42  // Retain cycle!
        }
    }
}

// CORRECT: Use [weak self] capture list
class MyClass {
    var value = 0
    
    func setup() {
        someAsyncWork { [weak self] in
            self?.value = 42  // No retain cycle
        }
    }
}

// WRONG: Using [weak self] but not unwrapping
someAsyncWork { [weak self] in
    self.value = 42  // Compile error: self is optional!
}

// CORRECT: Unwrap weak self
someAsyncWork { [weak self] in
    guard let self = self else { return }
    self.value = 42
}

// WRONG: Using @escaping when not needed
func doWork(action: @escaping () -> Void) {
    action()  // Called immediately — @escaping is unnecessary
}

// CORRECT: Remove @escaping for non-escaping closures
func doWork(action: () -> Void) {
    action()
}

// WRONG: Not using trailing closure syntax
execute(operation: { print("Hello") })

// CORRECT: Use trailing closure for cleaner code
execute { print("Hello") }

// WRONG: Force unwrapping in closure
let data = try! JSONDecoder().decode(MyType.self, from: jsonData)

// CORRECT: Handle errors in closure
do {
    let data = try JSONDecoder().decode(MyType.self, from: jsonData)
} catch {
    print("Decode error: \(error)")
}
```

## Gotchas
- Closures capture variables by reference by default. Use capture lists `[x = y]` to capture by value.
- `@escaping` closures can outlive the function they were passed to. Use `[weak self]` to prevent retain cycles.
- `[weak self]` makes `self` optional inside the closure. Use `guard let self = self else { return }` to unwrap.
- `[unowned self]` assumes self will never be nil during the closure's lifetime. Crashes if self is deallocated.
- Trailing closure syntax: if the last parameter is a function, the closure goes outside the parentheses.
- Multiple trailing closures (Swift 5.3+): label each closure with the parameter name.
- `@autoclosure` wraps an expression in a closure automatically. Useful for lazy evaluation (like `assert`).
- Shorthand argument names: `$0` for first, `$1` for second, etc. Use for short closures.
- Closures are reference types. Assigning a closure to a variable creates a reference to it.

## Related
- swift/stdlib/basics.md
- swift/stdlib/optionals.md
- swift/stdlib/collections.md
- swift/stdlib/protocols-generics.md
