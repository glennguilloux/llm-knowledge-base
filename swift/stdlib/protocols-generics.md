---
id: "swift-stdlib-protocols-generics"
title: "Swift Protocols and Generics: Conformance, Associated Types, and Opaque Types"
language: "swift"
category: "stdlib"
tags: ["swift", "protocols", "generics", "associated-types", "opaque-types", "some", "any"]
version: "5.9+"
retrieval_hint: "swift protocol definition extension conformance generic functions associated types some any keyword opaque types"
last_verified: "2026-05-24"
confidence: "high"
---

# Swift Protocols and Generics: Conformance, Associated Types, and Opaque Types

## When to Use
- Defining interfaces with protocols
- Writing generic functions and types
- Using associated types for type-safe abstractions
- Understanding `some` vs `any` keywords (Swift 5.7+)
- Extending types with protocol conformance

## Standard Pattern

```swift
// Protocol definition
protocol Drawable {
    var color: String { get set }
    func draw() -> String
    func area() -> Double
}

// Protocol conformance
struct Circle: Drawable {
    var color: String
    var radius: Double
    
    func draw() -> String {
        return "Drawing a \(color) circle with radius \(radius)"
    }
    
    func area() -> Double {
        return Double.pi * radius * radius
    }
}

struct Rectangle: Drawable {
    var color: String
    var width: Double
    var height: Double
    
    func draw() -> String {
        return "Drawing a \(color) rectangle \(width)x\(height)"
    }
    
    func area() -> Double {
        return width * height
    }
}

// Using protocols as types
func render(shape: Drawable) {
    print(shape.draw())
    print("Area: \(shape.area())")
}

// Protocol extension — provide default implementation
extension Drawable {
    func description() -> String {
        return "\(color) shape with area \(area())"
    }
}

// Generic function
func swapValues<T>(_ a: inout T, _ b: inout T) {
    let temp = a
    a = b
    b = temp
}

var x = 1, y = 2
swapValues(&x, &y)  // x=2, y=1

// Generic type
struct Stack<Element> {
    private var items: [Element] = []
    
    mutating func push(_ item: Element) {
        items.append(item)
    }
    
    @discardableResult
    mutating func pop() -> Element {
        return items.removeLast()
    }
    
    var top: Element? { items.last }
    var isEmpty: Bool { items.isEmpty }
}

var intStack = Stack<Int>()
intStack.push(1)
intStack.push(2)
print(intStack.pop()!)  // 2

// Generic constraints
func findIndex<T: Equatable>(of value: T, in array: [T]) -> Int? {
    for (index, item) in array.enumerated() {
        if item == value { return index }
    }
    return nil
}

// Protocol with associated type
protocol Container {
    associatedtype Item
    var count: Int { get }
    mutating func append(_ item: Item)
    subscript(i: Int) -> Item { get }
}

struct IntContainer: Container {
    typealias Item = Int
    var items: [Int] = []
    var count: Int { items.count }
    mutating func append(_ item: Int) { items.append(item) }
    subscript(i: Int) -> Int { items[i] }
}

// Opaque return type (some) — Swift 5.1+
func makeDrawable() -> some Drawable {
    return Circle(color: "red", radius: 5.0)
}
// Caller knows it's a Drawable, but not the concrete type

// Existential type (any) — Swift 5.7+
func drawShape(_ shape: any Drawable) {
    print(shape.draw())
}
// Can hold any type conforming to Drawable

// some vs any
// some: Compile-time type identity. More efficient, but must be single concrete type.
// any: Runtime type erasure. More flexible, but has performance cost.

// Protocol composition
func process(item: Drawable & CustomStringConvertible) {
    print(item.description())
    print(item.draw())
}

// Conditional conformance
extension Stack: Equatable where Element: Equatable {
    static func == (lhs: Stack<Element>, rhs: Stack<Element>) -> Bool {
        return lhs.items == rhs.items
    }
}

// Self requirement
protocol Copyable {
    func copy() -> Self
}

struct Point: Copyable {
    var x: Double
    var y: Double
    func copy() -> Point { Point(x: x, y: y) }
}
```

## Common Mistakes

```swift
// WRONG: Not using protocol extensions for default implementations
protocol Drawable {
    func draw() -> String
    func description() -> String  // Every conforming type must implement this!
}

// CORRECT: Provide default implementation in extension
protocol Drawable {
    func draw() -> String
}

extension Drawable {
    func description() -> String {  // Default implementation
        return "A drawable shape"
    }
}

// WRONG: Using any when some is more appropriate
func makeShape() -> any Drawable {
    return Circle(color: "red", radius: 5.0)
    // Returns existential type — has runtime overhead
}

// CORRECT: Use some when the concrete type is known at compile time
func makeShape() -> some Drawable {
    return Circle(color: "red", radius: 5.0)
    // More efficient — compiler knows the concrete type
}

// WRONG: Not constraining generics when needed
func process<T>(_ item: T) {
    print(item.count)  // Compile error: T doesn't have .count
}

// CORRECT: Add constraint
func process<T: Collection>(_ item: T) {
    print(item.count)  // OK — Collection has .count
}

// WRONG: Trying to use protocol with associated type as a type
func useContainer(_ container: Container) { }
// Compile error: Protocol with associated type can't be used as a type

// CORRECT: Use generic function instead
func useContainer<C: Container>(_ container: C) { }

// WRONG: Not using @discardableResult for functions where return value is optional
mutating func pop() -> Element {
    return items.removeLast()
}
// Warning: Result of call to pop() is unused

// CORRECT: Add @discardableResult
@discardableResult
mutating func pop() -> Element {
    return items.removeLast()
}
```

## Gotchas
- `some` (opaque type) hides the concrete type from the caller. The compiler still knows it. More efficient.
- `any` (existential type) can hold any conforming type. Has runtime overhead due to type erasure.
- Protocols with associated types (PATs) cannot be used as concrete types. Use generics instead.
- Protocol extensions provide default implementations. Conforming types can override them.
- `where` clauses add constraints to generics: `<T: Equatable>`, `<T: Codable & Hashable>`.
- `associatedtype` in protocols is like a generic type parameter. The conforming type chooses the concrete type.
- `Self` (capital S) refers to the conforming type. `self` (lowercase) refers to the instance.
- `@discardableResult` suppresses the "unused result" warning when the return value is intentionally ignored.
- Conditional conformance: `extension Array: Equatable where Element: Equatable`.

## Related
- swift/stdlib/basics.md
- swift/stdlib/closures.md
- swift/stdlib/collections.md
- swift/stdlib/error-handling.md
