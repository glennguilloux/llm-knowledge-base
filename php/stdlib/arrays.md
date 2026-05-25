---
id: "php-stdlib-arrays"
title: "PHP Arrays: Operations, Destructuring, and Merge Strategies"
language: "php"
category: "stdlib"
tags: ["php", "arrays", "array_map", "array_filter", "destructuring", "spread-operator", "array_merge"]
version: "8.2+"
retrieval_hint: "php array operations map filter reduce array_column spread operator destructuring array_merge"
last_verified: "2026-05-24"
confidence: "high"
---

# PHP Arrays: Operations, Destructuring, and Merge Strategies

## When to Use
- Transforming arrays with functional operations
- Extracting and reshaping array data
- Merging arrays with different strategies
- Destructuring arrays into variables

## Standard Pattern

```php
<?php

// Indexed arrays
$fruits = ['apple', 'banana', 'cherry'];

// Associative arrays (like dictionaries)
$user = [
    'name' => 'Alice',
    'email' => 'alice@example.com',
    'age' => 30,
    'roles' => ['admin', 'editor'],
];

// array_map — transform each element
$prices = [10.5, 20.0, 15.75];
$withTax = array_map(fn($p) => $p * 1.2, $prices);
// [12.6, 24.0, 18.9]

$names = ['alice', 'bob', 'charlie'];
$uppercased = array_map('strtoupper', $names);
// ['ALICE', 'BOB', 'CHARLIE']

// array_filter — filter elements
$numbers = [1, 2, 3, 4, 5, 6];
$even = array_filter($numbers, fn($n) => $n % 2 === 0);
// [2, 4, 6]
// Note: array_filter preserves keys!

$evenReindexed = array_values($even);  // [0 => 2, 1 => 4, 2 => 6]

// array_reduce — reduce to a single value
$sum = array_reduce($numbers, fn($carry, $n) => $carry + $n, 0);
// 21

// array_column — extract a column from array of arrays
$users = [
    ['name' => 'Alice', 'age' => 30],
    ['name' => 'Bob', 'age' => 25],
    ['name' => 'Charlie', 'age' => 35],
];
$names = array_column($users, 'name');
// ['Alice', 'Bob', 'Charlie']

// array_column with key
$usersByName = array_column($users, null, 'name');
// ['Alice' => ['name' => 'Alice', 'age' => 30], ...]

// List destructuring
[$first, $second, $third] = $fruits;
// $first = 'apple', $second = 'banana', $third = 'cherry'

// Associative destructuring
['name' => $name, 'email' => $email] = $user;
// $name = 'Alice', $email = 'alice@example.com'

// Spread operator (PHP 7.4+) for arrays
$arr1 = [1, 2, 3];
$arr2 = [4, 5, 6];
$merged = [...$arr1, ...$arr2];
// [1, 2, 3, 4, 5, 6]

$defaults = ['host' => 'localhost', 'port' => 3306, 'name' => 'mydb'];
$overrides = ['port' => 5432, 'name' => 'production'];
$config = [...$defaults, ...$overrides];
// ['host' => 'localhost', 'port' => 5432, 'name' => 'production']

// array_merge vs + operator — different merge strategies!
$a = ['a' => 1, 'b' => 2];
$b = ['b' => 3, 'c' => 4];

// array_merge: later values OVERWRITE earlier ones
$result = array_merge($a, $b);
// ['a' => 1, 'b' => 3, 'c' => 4]

// + operator: earlier values WIN (keeps first occurrence)
$result = $a + $b;
// ['a' => 1, 'b' => 2, 'c' => 4]

// String keys: array_merge overwrites, + keeps first
// Numeric keys: array_merge reindexes, + keeps first
$num1 = [10, 20, 30];
$num2 = [40, 50];
// array_merge: [10, 20, 30, 40, 50] (reindexed)
// + operator: [10, 20, 30] (keeps first)

// Useful array functions
$exists = in_array('apple', $fruits);     // true
$key = array_search('banana', $fruits);   // 1
$count = count($fruits);                  // 3
$isEmpty = empty($fruits);                // false
$hasKey = array_key_exists('name', $user); // true
$hasKey2 = key_exists('name', $user);      // alias

// Sorting
$numbers = [3, 1, 4, 1, 5];
sort($numbers);                          // Sorts in place, reindexes
asort($assocArray);                      // Sort by value, keep key association
ksort($assocArray);                      // Sort by key
usort($array, fn($a, $b) => $a <=> $b);  // Custom sort with spaceship
```

## Common Mistakes

```php
<?php

// WRONG: array_filter preserves keys — unexpected gaps
$filtered = array_filter([10, 20, 30], fn($n) => $n > 15);
// Keys preserved: [1 => 20, 2 => 30], not [0 => 20, 1 => 30]

// CORRECT: Use array_values to reindex if needed
$filtered = array_values(array_filter([10, 20, 30], fn($n) => $n > 15));
// [0 => 20, 1 => 30]

// WRONG: Confusing array_merge with + operator
$defaults = ['color' => 'red', 'size' => 'medium'];
$overrides = ['color' => 'blue'];
$result = $defaults + $overrides;
// ['color' => 'red', 'size' => 'medium'] — color is still 'red'!

// CORRECT: Use array_merge for overwriting behavior
$result = array_merge($defaults, $overrides);
// ['color' => 'blue', 'size' => 'medium']

// WRONG: Modifying array during foreach
foreach ($items as $key => $item) {
    if ($item['expired']) {
        unset($items[$key]);  // Works on $items copy but confusing
    }
}

// CORRECT: Use array_filter
$items = array_filter($items, fn($item) => !$item['expired']);

// WRONG: Not checking if key exists before access
$name = $user['name'];  // Warning/Error if 'name' key doesn't exist!

// CORRECT: Use null coalescing or check first
$name = $user['name'] ?? 'Unknown';
// or: $name = array_key_exists('name', $user) ? $user['name'] : 'Unknown';

// WRONG: Using references incorrectly in foreach
foreach ($items as &$item) {
    $item['processed'] = true;
}
unset($item);  // IMPORTANT: unset the reference after the loop!
// Without unset, $item still references the last element
```

## Gotchas
- `array_filter()` preserves array keys. Use `array_values()` to reindex if needed.
- `array_merge()` with numeric keys APPENDS and reindexes. With string keys, later values overwrite.
- The `+` operator keeps the FIRST occurrence of each key. It does NOT overwrite.
- `sort()`, `asort()`, `ksort()` modify the array in place and return `true`.
- Spread operator `...` works with arrays and Traversable objects (PHP 7.4+).
- `list()` and `[]` destructuring only work with arrays (not objects).
- `in_array()` uses loose comparison by default. Pass `true` as third arg for strict: `in_array($needle, $haystack, true)`.
- `array_search()` returns the key (not the value) or `false` if not found.

## Related
- php/stdlib/basics.md
- php/stdlib/string-operations.md
- php/web/laravel-basics.md
