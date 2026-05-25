---
id: "typescript-stdlib-array-operations"
title: "TypeScript Array Operations"
language: "typescript"
category: "stdlib"
subcategory: "collections"
tags: ["arrays", "map", "filter", "reduce", "destructuring", "spread", "sort"]
version: "5.0+"
retrieval_hint: "TypeScript array map filter reduce find sort destructuring spread operations"
last_verified: "2026-05-24"
confidence: "high"
---

# TypeScript Array Operations

## When to Use
- Transforming arrays with `map`, `filter`, `reduce`
- Searching arrays with `find`, `some`, `every`
- Flattening nested arrays with `flat`, `flatMap`
- Copying or combining arrays with spread and destructuring
- Sorting arrays (careful: `sort` mutates in place)

## Standard Pattern

```typescript
// map: transform each element
const numbers: number[] = [1, 2, 3, 4, 5];
const doubled: number[] = numbers.map((n): number => n * 2);
// [2, 4, 6, 8, 10]

// filter: keep elements matching predicate
const evens: number[] = numbers.filter((n): boolean => n % 2 === 0);
// [2, 4]

// reduce: accumulate into a single value
const sum: number = numbers.reduce((acc, n) => acc + n, 0);
// 15

// find: get first matching element
const found: number | undefined = numbers.find((n): boolean => n > 3);
// 4

// some: does at least one element match?
const hasLarge: boolean = numbers.some((n): boolean => n > 4);
// true

// every: do all elements match?
const allPositive: boolean = numbers.every((n): boolean => n > 0);
// true

// flat: flatten nested arrays
const nested: number[][] = [[1, 2], [3, 4], [5]];
const flatArray: number[] = nested.flat();
// [1, 2, 3, 4, 5]

// flatMap: map then flatten one level
const sentences: string[] = ["hello world", "foo bar"];
const words: string[] = sentences.flatMap((s) => s.split(" "));
// ["hello", "world", "foo", "bar"]

// destructuring
const [first, second, ...rest]: number[] = numbers;
// first=1, second=2, rest=[3,4,5]

// spread: copy or combine (non-mutating)
const copy: number[] = [...numbers];
const combined: number[] = [...numbers, 6, 7];

// sort: ALWAYS copy first to avoid mutation
const sorted: number[] = [...numbers].sort((a, b) => a - b);

// sort objects by property
interface Person {
  name: string;
  age: number;
}
const people: Person[] = [
  { name: "Alice", age: 30 },
  { name: "Bob", age: 25 },
  { name: "Charlie", age: 35 },
];
const byAge: Person[] = [...people].sort((a, b) => a.age - b.age);
```

## Common Mistakes

```typescript
// WRONG: sort() mutates the original array
const original = [3, 1, 2];
const sorted = original.sort();
// original is now [1, 2, 3] — it was mutated!

// CORRECT: spread into a new array before sorting
const original = [3, 1, 2];
const sorted = [...original].sort((a, b) => a - b);
// original is still [3, 1, 2]

// WRONG: using map when you don't need the returned array (use forEach or for-of)
const items = [1, 2, 3];
items.map((item) => {
  console.log(item);
});
// map creates a new unnecessary array of undefined values

// CORRECT: use forEach for side effects
const items = [1, 2, 3];
items.forEach((item) => {
  console.log(item);
});

// WRONG: forgetting the initial value in reduce (crashes on empty arrays)
const numbers: number[] = [];
const sum = numbers.reduce((acc, n) => acc + n);
// TypeError: Reduce of empty array with no initial value

// CORRECT: always provide an initial value
const numbers: number[] = [];
const sum = numbers.reduce((acc, n) => acc + n, 0);
// 0

// WRONG: using == in filter predicate (loose equality)
const values = [0, 1, "", "hello", null, undefined];
const truthy = values.filter((v) => v == true);
// [1] — misses "hello", includes nothing unexpected but logic is fragile

// CORRECT: use explicit boolean check
const values = [0, 1, "", "hello", null, undefined];
const truthy = values.filter((v): boolean => Boolean(v));
// [1, "hello"]

// WRONG: flat() only flattens one level by default
const deep = [[[1]], [[2]]];
const result = deep.flat();
// [[1], [2]] — still nested!

// CORRECT: specify depth or use Infinity
const deep = [[[1]], [[2]]];
const result = deep.flat(2);
// [1, 2]
// or: deep.flat(Infinity) for arbitrarily nested
```

## Gotchas
- `Array.prototype.sort()` mutates the original array and returns a reference to the same array — always copy first with `[...arr].sort()`.
- `sort()` without a comparator sorts **lexicographically**: `[10, 9, 2].sort()` produces `[10, 2, 9]`. Always pass `(a, b) => a - b` for numeric sort.
- `reduce` without an initial value uses the first element as the accumulator and skips it during iteration — this causes wrong results for transformations (e.g., `reduce` to build an object) and crashes on empty arrays.
- `map` always returns a new array of the same length — you cannot use it to conditionally skip elements. Use `filter` + `map` or `flatMap` with an empty array return.
- `find` returns `undefined` when nothing matches — always handle the `undefined` case; TypeScript's strict mode will enforce this.
- `flat(Infinity)` works for arbitrarily deep nesting but can be slow on very large/deep structures.
- Spread (`...`) creates a **shallow** copy — nested objects/arrays are still shared references. Use `structuredClone()` or a library for deep copies.

## Related
- typescript/stdlib/generics.md
- typescript/stdlib/error-handling.md
