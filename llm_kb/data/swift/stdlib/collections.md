---
id: "swift-stdlib-collections"
title: "Swift Collections: Array, Dictionary, Set, and Higher-Order Functions"
language: "swift"
category: "stdlib"
tags: ["swift", "collections", "array", "dictionary", "set", "map", "filter", "reduce"]
version: "5.9+"
retrieval_hint: "swift Array Dictionary Set higher-order functions map filter reduce subscripting iterating"
last_verified: "2026-05-24"
confidence: "high"
---

# Swift Collections: Array, Dictionary, Set, and Higher-Order Functions

## When to Use
- Working with collections of data in Swift
- Transforming, filtering, or reducing collections
- Choosing between Array, Dictionary, and Set
- Using functional programming patterns with collections

## Standard Pattern

```swift
// Array — ordered collection
var fruits: [String] = ["apple", "banana", "cherry"]
fruits.append("date")
fruits.insert("avocado", at: 0)
fruits.remove(at: 1)
let count = fruits.count
let first = fruits.first  // Optional<String>
let contains = fruits.contains("banana")

// Array with type inference
let numbers = [1, 2, 3, 4, 5]  // [Int]
let empty: [Int] = []           // Empty array

// Dictionary — key-value pairs
var scores: [String: Int] = ["Alice": 95, "Bob": 87, "Charlie": 92]
scores["Alice"] = 98            // Update value
scores["Dave"] = 85            // Add new key-value
scores["Bob"] = nil            // Remove key
let aliceScore = scores["Alice"]  // Optional<Int>

// Dictionary with default value
let bobScore = scores["Bob", default: 0]  // Returns 0 if key not found

// Set — unordered unique values
let uniqueNumbers: Set<Int> = [1, 2, 3, 3, 4]  // {1, 2, 3, 4}
var tags: Set<String> = ["swift", "ios"]
tags.insert("swift")  // No effect — already exists
tags.insert("macos")  // Added

// Set operations
let setA: Set = [1, 2, 3, 4]
let setB: Set = [3, 4, 5, 6]
let intersection = setA.intersection(setB)  // {3, 4}
let union = setA.union(setB)                // {1, 2, 3, 4, 5, 6}
let difference = setA.subtracting(setB)     // {1, 2}

// Higher-order functions
let numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

// map — transform each element
let doubled = numbers.map { $0 * 2 }
// [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]

let strings = numbers.map { "Number: \($0)" }

// filter — keep elements matching predicate
let even = numbers.filter { $0 % 2 == 0 }
// [2, 4, 6, 8, 10]

// reduce — combine all elements into single value
let sum = numbers.reduce(0, +)  // 55
let product = numbers.reduce(1, *)

// compactMap — map and remove nil values
let strings = ["1", "2", "three", "4"]
let ints = strings.compactMap { Int($0) }  // [1, 2, 4]

// flatMap — map and flatten (for nested collections)
let nested = [[1, 2], [3, 4], [5, 6]]
let flat = nested.flatMap { $0 }  // [1, 2, 3, 4, 5, 6]

// Chaining operations
let result = numbers
    .filter { $0 % 2 == 0 }
    .map { $0 * $0 }
    .prefix(3)
// [4, 16, 36]

// forEach — iterate with side effects
fruits.forEach { print($0) }

// sorted
let sorted = numbers.sorted(by: >)  // Descending
let sortedStrings = fruits.sorted()  // Alphabetical

// Dictionary operations
let names = ["Alice", "Bob", "Charlie"]
let nameLengths = names.reduce(into: [String: Int]()) { result, name in
    result[name] = name.count
}
// ["Alice": 5, "Bob": 3, "Charlie": 7]

// Grouping
let words = ["apple", "banana", "avocado", "cherry", "blueberry"]
let byFirstLetter = Dictionary(grouping: words, by: { $0.first! })
// ["a": ["apple", "avocado"], "b": ["banana", "blueberry"], "c": ["cherry"]]

// Iterating with indices
for (index, fruit) in fruits.enumerated() {
    print("\(index): \(fruit)")
}

// Safe subscripting
extension Array {
    subscript(safe index: Int) -> Element? {
        return indices.contains(index) ? self[index] : nil
    }
}
let item = fruits[safe: 10]  // nil instead of crash
```

## Common Mistakes

```swift
// WRONG: Accessing array index out of bounds
let items = [1, 2, 3]
let item = items[5]  // Runtime crash: Index out of bounds

// CORRECT: Check bounds or use safe access
if items.count > 5 {
    let item = items[5]
}
// Or use safe subscript extension

// WRONG: Force unwrapping dictionary lookup
let scores = ["Alice": 95]
let bobScore = scores["Bob"]!  // Runtime crash: nil!

// CORRECT: Use optional binding or default value
if let score = scores["Bob"] {
    print(score)
}
// Or:
let bobScore = scores["Bob", default: 0]

// WRONG: Modifying array during iteration
var numbers = [1, 2, 3, 4, 5]
for number in numbers {
    if number % 2 == 0 {
        // numbers.remove(...) — Would crash! Can't modify during iteration
    }
}

// CORRECT: Use filter to create new array
numbers = numbers.filter { $0 % 2 != 0 }

// WRONG: Using map when you don't need the return value (use forEach)
let _ = items.map { print($0) }  // Creates unnecessary array of Void

// CORRECT: Use forEach for side effects
items.forEach { print($0) }

// WRONG: Not using compactMap when transforming to optional values
let strings = ["1", "2", "three"]
let ints = strings.map { Int($0) }  // [Optional(1), Optional(2), nil]

// CORRECT: Use compactMap to remove nils
let ints = strings.compactMap { Int($0) }  // [1, 2]

// WRONG: Confusing flatMap with map for nested arrays
let nested = [[1, 2], [3, 4]]
let wrong = nested.map { $0 }  // [[1, 2], [3, 4]] — still nested!

// CORRECT: Use flatMap to flatten
let correct = nested.flatMap { $0 }  // [1, 2, 3, 4]
```

## Gotchas
- Arrays are value types in Swift (copied on assignment). Use `inout` or `NSMutableArray` for reference semantics.
- Dictionary lookup returns an `Optional`. Always handle the nil case.
- `Set` requires elements to conform to `Hashable`. Most standard library types already do.
- `map`, `filter`, `reduce` return NEW collections. They don't modify the original.
- `compactMap` is `map` + `nil` removal. Use it when your transformation can fail.
- `flatMap` flattens nested collections. For optional unwrapping, use `compactMap` (Swift 4.1+).
- `reduce(into:_:)` is more efficient for building collections (avoids copying).
- `enumerated()` returns `(offset, element)` tuples. The offset is NOT always the index (for slices).
- Swift arrays use copy-on-write. Multiple arrays share the same storage until one is mutated.

## Related
- swift/stdlib/basics.md
- swift/stdlib/optionals.md
- swift/stdlib/closures.md
- swift/stdlib/protocols-generics.md
