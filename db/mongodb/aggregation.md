---
id: "db-mongodb-aggregation"
title: "MongoDB Aggregation Pipeline"
language: "javascript"
category: "db"
subcategory: "aggregation"
tags: ["mongodb", "aggregation", "pipeline", "match", "group", "lookup"]
version: "6.0+"
retrieval_hint: "MongoDB aggregation pipeline match group lookup"
last_verified: "2026-05-24"
confidence: "high"
---

# MongoDB Aggregation Pipeline

## When to Use
- Complex data transformations
- Grouping and aggregation
- Joining collections
- Data analysis and reporting

## Standard Pattern

```javascript
// Basic aggregation pipeline
db.orders.aggregate([
  // Stage 1: Filter
  { $match: { status: "completed", createdAt: { $gte: ISODate("2024-01-01") } } },
  
  // Stage 2: Group
  { $group: {
    _id: "$customerId",
    totalSpent: { $sum: "$total" },
    orderCount: { $sum: 1 },
    avgOrder: { $avg: "$total" }
  }},
  
  // Stage 3: Sort
  { $sort: { totalSpent: -1 } },
  
  // Stage 4: Limit
  { $limit: 10 }
]);

// Join collections (lookup)
db.orders.aggregate([
  { $lookup: {
    from: "users",
    localField: "customerId",
    foreignField: "_id",
    as: "customer"
  }},
  { $unwind: "$customer" },
  { $project: {
    orderId: "$_id",
    customerName: "$customer.name",
    total: 1,
    status: 1
  }}
]);

// Group by date
db.orders.aggregate([
  { $group: {
    _id: {
      year: { $year: "$createdAt" },
      month: { $month: "$createdAt" }
    },
    revenue: { $sum: "$total" },
    count: { $sum: 1 }
  }},
  { $sort: { "_id.year": -1, "_id.month": -1 } }
]);

// Conditional aggregation
db.orders.aggregate([
  { $group: {
    _id: null,
    completedRevenue: {
      $sum: { $cond: [{ $eq: ["$status", "completed"] }, "$total", 0] }
    },
    pendingRevenue: {
      $sum: { $cond: [{ $eq: ["$status", "pending"] }, "$total", 0] }
    }
  }}
]);
```

## Common Mistakes

```javascript
// WRONG: Using $match after $group (filters aggregated results)
db.orders.aggregate([
  { $group: { _id: "$status", total: { $sum: "$total" } } },
  { $match: { status: "completed" } }  // Wrong field name!
]);

// CORRECT: $match before $group for pre-filtering
db.orders.aggregate([
  { $match: { status: "completed" } },
  { $group: { _id: "$customerId", total: { $sum: "$total" } } }
]);

// WRONG: Not using index with $match
db.orders.aggregate([
  { $match: { status: "completed" } }  // No index on status!
]);

// CORRECT: Create index for frequently queried fields
db.orders.createIndex({ status: 1, createdAt: -1 });

// WRONG: Using $sort after $limit — gets wrong top-N results
db.orders.aggregate([
  { $match: { status: "completed" } },
  { $limit: 10 },
  { $sort: { total: -1 } },  // sorts only 10 arbitrary docs, not top 10!
]);

// CORRECT: $sort before $limit to get actual top-N
db.orders.aggregate([
  { $match: { status: "completed" } },
  { $sort: { total: -1 } },
  { $limit: 10 },
]);
```

## Gotchas
- `$match` should be early in the pipeline for performance
- `$lookup` is like SQL JOIN — use sparingly for performance
- `$unwind` deconstructs arrays into individual documents
- `$project` shapes the output (include/exclude fields)
- Use `$cond` for conditional logic within stages
- Pipeline stages are executed in order
- Use `explain()` to analyze pipeline performance

## Related
- db/postgres/json-queries.md
- python/db/redis/basics.md
