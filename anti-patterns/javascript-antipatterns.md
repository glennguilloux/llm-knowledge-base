---
id: "antipatterns-javascript"
title: "JavaScript Anti-Patterns"
language: "javascript"
category: "anti-patterns"
tags: ["antipatterns", "javascript", "common-mistakes", "es6", "async"]
version: "n/a"
retrieval_hint: "javascript common mistakes equality coercion var hoisting callback hell promise swallowing"
last_verified: "2026-05-24"
confidence: "high"
---

# JavaScript Anti-Patterns

## When to Use
- Reviewing JavaScript code for common mistakes
- Training small LLMs to avoid frequent JavaScript errors
- Code review checklists
- Onboarding developers new to JavaScript

## Standard Pattern

```javascript
// WRONG: Using var instead of const/let
for (var i = 0; i < 5; i++) {
  setTimeout(() => console.log(i)); // prints 5,5,5,5,5
}

// CORRECT: Use const/let for block scoping
for (let i = 0; i < 5; i++) {
  setTimeout(() => console.log(i)); // prints 0,1,2,3,4
}

// WRONG: Using == instead of ===
console.log(0 == "");       // true (coercion)
console.log(null == undefined); // true
console.log([1] == 1);      // true

// CORRECT: Use strict equality ===
console.log(0 === "");       // false
console.log(null === undefined); // false
console.log([1] === 1);      // false

// WRONG: Swallowing promise errors
fetch("/api/data")
  .then(res => res.json())
  .then(data => this.setState({ data }));
// Missing .catch() — silent failure

// CORRECT: Always handle promise errors
fetch("/api/data")
  .then(res => {
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  })
  .then(data => this.setState({ data }))
  .catch(err => console.error("Fetch failed:", err));

// WRONG: Callback hell
getUser(id, (user) => {
  getOrders(user.id, (orders) => {
    getItems(orders[0].id, (items) => {
      getReviews(items[0].id, (reviews) => {
        console.log(reviews);
      });
    });
  });
});

// CORRECT: Use async/await
async function getReviewData(id) {
  const user = await getUser(id);
  const orders = await getOrders(user.id);
  const items = await getItems(orders[0].id);
  const reviews = await getReviews(items[0].id);
  return reviews;
}

// WRONG: Modifying function parameters
function processUser(user) {
  user.name = user.name.trim();  // mutates caller's object
  user.role = "active";          // unexpected side effect
  return user;
}

// CORRECT: Return new object
function processUser(user) {
  return {
    ...user,
    name: user.name.trim(),
    role: "active",
  };
}

// WRONG: typeof checks instead of proper type checking
if (typeof value === "array") {  // always false! typeof [] === "object"
  console.log("array");
}

// CORRECT: Use Array.isArray
if (Array.isArray(value)) {
  console.log("array");
}

// WRONG: Not using optional chaining
const city = user && user.address && user.address.city;

// CORRECT: Optional chaining (ES2020+)
const city = user?.address?.city;
```

## Common Mistakes
The most frequent JavaScript anti-patterns are using `var` (hoisting bugs, no block scoping), loose equality (`==` instead of `===` leading to coercion surprises), and missing error handling on promises (silent failures). Callback hell reduces readability and makes error handling nearly impossible. Mutating function parameters creates hidden side effects that are hard to debug. The `typeof` operator is unreliable for arrays and null — use `Array.isArray()` and strict null checks instead.

## Gotchas
- `typeof null === "object"` — this is a 25-year-old JS bug, use `value === null` instead
- `typeof [] === "object"` — use `Array.isArray()` for array detection
- `NaN !== NaN` — use `Number.isNaN()` for NaN checks, not `===`
- `==` coerces types: `0 == ""` is `true`, `[] == false` is `true`
- `var` is function-scoped, not block-scoped — `let`/`const` avoid hoisting bugs
- `const` prevents reassignment, NOT mutation — `const arr = []; arr.push(1)` works
- Missing `await` on async function returns a Promise, not the value
- `for...in` iterates object keys (including prototype), `for...of` iterates values
- `JSON.stringify` drops `undefined`, functions, and symbols — not safe for all serialization

## Related
- typescript/stdlib/async-patterns.md
- typescript/web/react/hooks.md
- anti-patterns/typescript-antipatterns.md
